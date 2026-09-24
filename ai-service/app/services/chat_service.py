"""Chat responses and public progress events from the existing agent graph."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any
from uuid import uuid4

from langsmith import get_current_run_tree, set_run_metadata, trace

from app.ai.agent.graph import MAX_QUERY_RETRIES, procurement_graph
from app.models.chat import ChatResponse
from app.observability import normalize_request_id
from app.services.conversation_service import (
    finish_turn,
    load_chat_history,
    load_query_context,
    start_turn,
)

logger = logging.getLogger(__name__)
PUBLIC_FAILURE_MESSAGE = "The assistant could not finish this response. Please try again."

TRACE_NAME = "procurement-agent-request"
TRACE_TAGS = ["procurement-ai", "chat-request"]


def trace_outcome(state: dict[str, Any]) -> str:
    """Map the final graph state to a stable operational outcome."""
    if state.get("route_category") == "analytical":
        if state.get("execution_error"):
            return "execution_failure"
        if state.get("validation_error") and not state.get("is_valid"):
            return "validation_failure"
    return "success"


def trace_metadata(
    *,
    request_id: str,
    conversation_id: str,
    turn_id: str,
    state: dict[str, Any],
    outcome: str,
) -> dict[str, Any]:
    retry_count = state.get("retry_count", 0)
    return {
        "request_id": request_id,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "environment": os.getenv("APP_ENV", "development"),
        "route_category": state.get("route_category") or "unknown",
        "outcome": outcome,
        "retry_count": retry_count if isinstance(retry_count, int) else 0,
        "has_visualization": bool(state.get("visualization")),
    }


def update_trace_metadata(
    *,
    trace_context: Any | None = None,
    **metadata: Any,
) -> None:
    """Update the root trace even after nested LangGraph runs change context."""
    trace_run = getattr(trace_context, "new_run", trace_context)
    if trace_run is not None and hasattr(trace_run, "metadata"):
        trace_run.metadata.update(metadata)
        return
    if get_current_run_tree() is not None:
        set_run_metadata(**metadata)


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


def chat_response(
    conversation_id: str,
    state: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    request_id = normalize_request_id(request_id)
    is_analytical = state.get("route_category", "analytical") == "analytical"
    can_visualize = state.get("route_category") in (
        "analytical",
        "contextual_content",
    )

    return ChatResponse(
        request_id=request_id,
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


def agent_config(
    *,
    request_id: str,
    conversation_id: str,
    turn_id: str,
) -> dict[str, Any]:
    """Correlate the graph and all child runs with the originating request."""
    return {
        "configurable": {"thread_id": conversation_id},
        "run_name": "procurement-agent",
        "tags": ["procurement-ai", "chat-request"],
        "metadata": {
            "request_id": request_id,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
        },
    }


def process_chat_message(
    message: str,
    conversation_id: str | None = None,
    *,
    request_id: str | None = None,
):
    request_id = normalize_request_id(request_id)
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
        request_id=request_id,
    )
    try:
        with trace(
            TRACE_NAME,
            run_type="chain",
            inputs={"question": message},
            metadata=trace_metadata(
                request_id=request_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                state=state,
                outcome="in_progress",
            ),
            tags=TRACE_TAGS,
        ) as root_trace:
            try:
                result = procurement_graph.invoke(
                    state,
                    config=agent_config(
                        request_id=request_id,
                        conversation_id=conversation_id,
                        turn_id=turn_id,
                    ),
                )
                response = chat_response(
                    conversation_id,
                    result,
                    request_id=request_id,
                )
                finish_turn(
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    response=response,
                    query_context=reusable_query_context(result),
                )
                update_trace_metadata(trace_context=root_trace, **trace_metadata(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    state=result,
                    outcome=trace_outcome(result),
                ))
                return response
            except Exception:
                update_trace_metadata(trace_context=root_trace, **trace_metadata(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    state=state,
                    outcome="agent_failure",
                ))
                raise
    except Exception:
        finish_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            response=chat_response(
                conversation_id,
                {**state, "answer": PUBLIC_FAILURE_MESSAGE},
                request_id=request_id,
            ),
            status="error",
        )
        raise


def progress(step: str, status: str, label: str) -> dict[str, Any]:
    return {"type": "progress", "step": step, "status": status, "label": label}


async def stream_chat_message(
    message: str,
    conversation_id: str | None = None,
    *,
    request_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Allowlist public artifacts; never forward raw graph state or reasoning."""
    request_id = normalize_request_id(request_id)
    existing_conversation_id = conversation_id
    conversation_id = conversation_id or str(uuid4())
    turn_id = str(uuid4())
    state = initial_state(message)
    finished = False
    persisted = False
    started = False
    trace_run = None
    trace_open = False

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
            request_id=request_id,
        )
        started = True
        trace_run = trace(
            TRACE_NAME,
            run_type="chain",
            inputs={"question": message},
            metadata=trace_metadata(
                request_id=request_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                state=state,
                outcome="in_progress",
            ),
            tags=TRACE_TAGS,
        )
        await trace_run.__aenter__()
        trace_open = True
        yield {
            "type": "start",
            "request_id": request_id,
            "conversation_id": conversation_id,
        }
        yield progress("route_question", "running", "Understanding your request")
        async with aclosing(procurement_graph.astream(
            state,
            config=agent_config(
                request_id=request_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
            ),
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
        response = chat_response(
            conversation_id,
            state,
            request_id=request_id,
        )
        finish_turn(
            conversation_id=conversation_id,
            turn_id=turn_id,
            response=response,
            query_context=reusable_query_context(state),
        )
        persisted = True
        update_trace_metadata(trace_context=trace_run, **trace_metadata(
            request_id=request_id,
            conversation_id=conversation_id,
            turn_id=turn_id,
            state=state,
            outcome=trace_outcome(state),
        ))
        await trace_run.__aexit__(None, None, None)
        trace_open = False
        yield {"type": "done", **response}
    except asyncio.CancelledError:
        update_trace_metadata(trace_context=trace_run, **trace_metadata(
            request_id=request_id,
            conversation_id=conversation_id,
            turn_id=turn_id,
            state=state,
            outcome="cancelled",
        ))
        if trace_open and trace_run is not None:
            await trace_run.__aexit__(None, None, None)
            trace_open = False
        raise
    except Exception as error:
        update_trace_metadata(trace_context=trace_run, **trace_metadata(
            request_id=request_id,
            conversation_id=conversation_id,
            turn_id=turn_id,
            state=state,
            outcome="agent_failure",
        ))
        if trace_open and trace_run is not None:
            await trace_run.__aexit__(
                type(error),
                error,
                error.__traceback__,
            )
            trace_open = False
        logger.exception("AI assistant stream failed request_id=%s", request_id)
        try:
            finish_turn(
                conversation_id=conversation_id,
                turn_id=turn_id,
                response=chat_response(
                    conversation_id,
                    {**state, "answer": PUBLIC_FAILURE_MESSAGE},
                    request_id=request_id,
                ),
                status="error",
            )
            persisted = True
        except Exception:
            logger.exception(
                "Could not persist failed AI assistant turn request_id=%s",
                request_id,
            )
        yield {
            "type": "error",
            "request_id": request_id,
            "message": PUBLIC_FAILURE_MESSAGE,
        }
    finally:
        if trace_open and trace_run is not None:
            update_trace_metadata(trace_context=trace_run, **trace_metadata(
                request_id=request_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                state=state,
                outcome="cancelled",
            ))
            await trace_run.__aexit__(None, None, None)
        if started and not persisted:
            try:
                finish_turn(
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    response=chat_response(
                        conversation_id,
                        {**state, "answer": PUBLIC_FAILURE_MESSAGE},
                        request_id=request_id,
                    ),
                    status="error",
                )
            except Exception:
                logger.exception(
                    "Could not persist failed AI assistant turn request_id=%s",
                    request_id,
                )
