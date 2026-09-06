"""Chat responses and public progress events from the existing agent graph."""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any
from uuid import uuid4

from app.ai.agent.graph import MAX_QUERY_RETRIES, procurement_graph
from app.models.chat import ChatResponse

logger = logging.getLogger(__name__)


def initial_state(message: str) -> dict[str, Any]:
    # Checkpoints retain history, but results/errors must never leak across turns.
    return {
        "question": message,
        "retry_count": 0,
        "pipeline": [],
        "query_description": "",
        "is_valid": False,
        "validation_error": None,
        "query_result": [],
        "result_count": 0,
        "execution_error": None,
        "answer": "",
    }


def chat_response(conversation_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return ChatResponse(
        conversation_id=conversation_id,
        answer=state.get("answer") or "I was unable to answer that question.",
        query_description=state.get("query_description"),
        pipeline=state.get("pipeline"),
        result_count=state.get("result_count", 0),
        retry_count=state.get("retry_count", 0),
    ).model_dump(mode="json")


def process_chat_message(message: str, conversation_id: str | None = None):
    conversation_id = conversation_id or str(uuid4())
    result = procurement_graph.invoke(
        initial_state(message),
        config={"configurable": {"thread_id": conversation_id}},
    )
    return chat_response(conversation_id, result)


def progress(step: str, status: str, label: str) -> dict[str, Any]:
    return {"type": "progress", "step": step, "status": status, "label": label}


async def stream_chat_message(
    message: str, conversation_id: str | None = None
) -> AsyncIterator[dict[str, Any]]:
    """Allowlist public artifacts; never forward raw graph state or reasoning."""
    conversation_id = conversation_id or str(uuid4())
    state = initial_state(message)
    finished = False
    yield {"type": "start", "conversation_id": conversation_id}
    yield progress("generate_query", "running", "Generating MongoDB query")

    try:
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
                    if metadata.get("langgraph_node") == "generate_answer":
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
                    if node in ("generate_query", "correct_query"):
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
                    elif node in ("generate_answer", "validation_failure"):
                        yield progress("generate_answer", "complete", "Response prepared")
                    elif node == "save_conversation":
                        finished = True
        # Finish checkpoint writes before the client receives the terminal event
        # and closes its stream or submits a follow-up question.
        if not finished:
            raise RuntimeError("The agent ended without saving the conversation.")
        yield {"type": "done", **chat_response(conversation_id, state)}
    except Exception:
        logger.exception("AI assistant stream failed")
        yield {
            "type": "error",
            "message": "The assistant could not finish this response. Please try again.",
        }
