"""Chat responses and public progress events from the existing agent graph."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any
from uuid import uuid4

from app.ai.agent.graph import MAX_QUERY_RETRIES, procurement_graph
from app.models.chat import ChatResponse
from app.services.conversation_service import (
    finish_turn,
    load_chat_history,
    load_query_context,
    start_turn,
)

logger = logging.getLogger(__name__)
PUBLIC_FAILURE_MESSAGE = "The assistant could not finish this response. Please try again."


def initial_state(
    message: str,
    chat_history: list[dict[str, str]] | None = None,
    query_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Current-turn artifacts are reset. Reusable context is loaded into
    # separate fields and can only be selected by the contextual route.
    state = {
        "question": message,
        "chat_history": chat_history or [],
        "route_category": "analytical",
        "wants_visualization": False,
        "visualization_type": "none",
        "retry_count": 0,
        "pipeline": [],
        "query_description": "",
        "is_valid": False,
        "validation_error": None,
        "query_result": [],
        "result_count": 0,
        "execution_error": None,
        "has_contextual_data": False,
        "contextual_query_result": [],
        "contextual_query_description": "",
        "contextual_pipeline": [],
        "contextual_result_count": 0,
        "visualization": None,
        "answer": "",
    }
    if query_context is not None:
        state.update({
            "has_contextual_data": True,
            "contextual_query_result": query_context.get("query_result", []),
            "contextual_query_description": query_context.get(
                "query_description", ""
            ),
            "contextual_pipeline": query_context.get("pipeline", []),
            "contextual_result_count": query_context.get("result_count", 0),
        })
    return state


def reusable_query_context(state: dict[str, Any]) -> dict[str, Any] | None:
    if not state.get("has_contextual_data", False):
        return None
    return {
        "query_result": state.get("contextual_query_result", []),
        "query_description": state.get("contextual_query_description", ""),
        "pipeline": state.get("contextual_pipeline", []),
        "result_count": state.get("contextual_result_count", 0),
    }


def visualization_payload(state: dict[str, Any]) -> dict[str, Any] | None:
    visualization = state.get("visualization")
    if visualization is None:
        return None
    if isinstance(visualization, dict):
        return visualization
    return visualization.model_dump(mode="json")


def chat_response(conversation_id: str, state: dict[str, Any]) -> dict[str, Any]:
    is_analytical = state.get("route_category", "analytical") == "analytical"
    can_visualize = state.get("route_category") in (
        "analytical",
        "contextual_content",
    )

    return ChatResponse(
        conversation_id=conversation_id,
        answer=state.get("answer") or "I was unable to answer that question.",
        query_description=state.get("query_description") if is_analytical else None,
        pipeline=state.get("pipeline") if is_analytical else None,
        result_count=state.get("result_count", 0) if is_analytical else 0,
        retry_count=state.get("retry_count", 0) if is_analytical else 0,
        visualization=(
            visualization_payload(state)
            if can_visualize
            else None
        ),
    ).model_dump(mode="json")


def process_chat_message(message: str, conversation_id: str | None = None):
    existing_conversation_id = conversation_id
    conversation_id = conversation_id or str(uuid4())
    turn_id = str(uuid4())
    state = initial_state(
        message,
        load_chat_history(existing_conversation_id),
        load_query_context(existing_conversation_id),
    )
    start_turn(
        conversation_id=conversation_id,
        turn_id=turn_id,
        question=message,
    )
    try:
        result = procurement_graph.invoke(
            state,
            config={"configurable": {"thread_id": conversation_id}},
        )
        response = chat_response(conversation_id, result)
        finish_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            response=response,
            query_context=reusable_query_context(result),
        )
        return response
    except Exception:
        finish_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            response=chat_response(
                conversation_id,
                {**state, "answer": PUBLIC_FAILURE_MESSAGE},
            ),
            status="error",
        )
        raise


def progress(step: str, status: str, label: str) -> dict[str, Any]:
    return {"type": "progress", "step": step, "status": status, "label": label}


async def stream_chat_message(
    message: str, conversation_id: str | None = None
) -> AsyncIterator[dict[str, Any]]:
    """Allowlist public artifacts; never forward raw graph state or reasoning."""
    existing_conversation_id = conversation_id
    conversation_id = conversation_id or str(uuid4())
    turn_id = str(uuid4())
    state = initial_state(message)
    finished = False
    persisted = False
    started = False

    try:
        state = initial_state(
            message,
            load_chat_history(existing_conversation_id),
            load_query_context(existing_conversation_id),
        )
        start_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            question=message,
        )
        started = True
        yield {"type": "start", "conversation_id": conversation_id}
        yield progress("route_question", "running", "Understanding your request")
        async with aclosing(procurement_graph.astream(
            state,
            config={"configurable": {"thread_id": conversation_id}},
            stream_mode=["updates", "messages"],
        )) as events:
            async for mode, chunk in events:
                if mode == "messages":
                    token, metadata = chunk
                    # Only final answer text belongs in the chat. Do not expose
                    # structured query tokens, reasoning, or tool-call blocks.
                    if metadata.get("langgraph_node") in (
                        "generate_answer",
                        "contextual_content",
                    ):
                        content = token.content
                        if isinstance(content, list):
                            content = "".join(
                                block.get("text", "")
                                for block in content
                                if isinstance(block, dict) and block.get("type") == "text"
                            )
                        if isinstance(content, str) and content:
                            yield {"type": "answer_delta", "text": content}
                    continue

                for node, update in chunk.items():
                    if not isinstance(update, dict):
                        continue
                    state.update(update)
                    if node == "route_question":
                        yield progress(node, "complete", "Request understood")
                        if state.get("route_category") == "analytical":
                            yield progress("generate_query", "running", "Generating MongoDB query")
                        elif state.get("route_category") == "contextual_content":
                            yield progress(
                                "contextual_content",
                                "running",
                                "Using the previous result",
                            )
                        else:
                            yield progress("generate_direct_response", "running", "Preparing response")
                    elif node == "generate_direct_response":
                        yield progress(node, "complete", "Response prepared")
                        if state.get("answer"):
                            yield {"type": "answer_delta", "text": state["answer"]}
                    elif node == "contextual_content":
                        yield progress(
                            node,
                            "complete",
                            "Previous result reused",
                        )
                        if (
                            state.get("wants_visualization")
                            and state.get("query_result")
                        ):
                            yield progress(
                                "generate_visualization",
                                "running",
                                "Creating visualization",
                            )
                    elif node in ("generate_query", "correct_query"):
                        yield progress(node, "complete", "Query generated" if node == "generate_query" else "Query corrected")
                        yield {
                            "type": "query",
                            "pipeline": state.get("pipeline", []),
                            "query_description": state.get("query_description", ""),
                            "retry_count": state.get("retry_count", 0),
                        }
                        yield progress("validate_query", "running", "Validating query safety")
                    elif node == "validate_query":
                        if state.get("is_valid"):
                            yield progress(node, "complete", "Query passed safety checks")
                            yield progress("execute_query", "running", "Querying procurement data")
                        else:
                            yield progress(node, "error", "Query did not pass safety checks")
                            if state.get("retry_count", 0) < MAX_QUERY_RETRIES:
                                yield progress("correct_query", "running", f"Correcting query · attempt {state.get('retry_count', 0) + 1}")
                    elif node == "execute_query":
                        failed = bool(state.get("execution_error"))
                        yield progress(node, "error" if failed else "complete", "Could not retrieve data" if failed else "Procurement results retrieved")
                        yield progress("generate_answer", "running", "Preparing response")
                    elif node == "generate_visualization":
                        yield progress(node, "complete", "Visualization prepared")
                        if state.get("visualization"):
                            yield {
                                "type": "visualization",
                                "visualization": visualization_payload(state),
                            }
                    elif node == "generate_answer":
                        yield progress("generate_answer", "complete", "Response prepared")
                        if (
                            state.get("wants_visualization")
                            and state.get("query_result")
                            and not state.get("execution_error")
                        ):
                            yield progress(
                                "generate_visualization",
                                "running",
                                "Creating visualization",
                            )
                    elif node == "validation_failure":
                        yield progress("generate_answer", "complete", "Response prepared")
                    elif node == "save_conversation":
                        finished = True
        # Finish checkpoint writes before the client receives the terminal event
        # and closes its stream or submits a follow-up question.
        if not finished:
            raise RuntimeError("The agent ended without saving the conversation.")
        response = chat_response(conversation_id, state)
        finish_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            response=response,
            query_context=reusable_query_context(state),
        )
        persisted = True
        yield {"type": "done", **response}
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("AI assistant stream failed")
        try:
            finish_turn(
                conversation_id=conversation_id,
                turn_id=turn_id,
                response=chat_response(
                    conversation_id,
                    {**state, "answer": PUBLIC_FAILURE_MESSAGE},
                ),
                status="error",
            )
            persisted = True
        except Exception:
            logger.exception("Could not persist failed AI assistant turn")
        yield {
            "type": "error",
            "message": PUBLIC_FAILURE_MESSAGE,
        }
    finally:
        if started and not persisted:
            try:
                finish_turn(
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    response=chat_response(
                        conversation_id,
                        {**state, "answer": PUBLIC_FAILURE_MESSAGE},
                    ),
                    status="error",
                )
            except Exception:
                logger.exception("Could not persist failed AI assistant turn")
