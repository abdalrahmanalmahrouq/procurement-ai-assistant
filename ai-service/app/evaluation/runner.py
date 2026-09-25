"""Run versioned evaluation cases against the real LangGraph workflow."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.ai.agent.graph import procurement_graph
from app.evaluation.dataset import CASES_BY_ID
from app.services.chat_service import agent_config, initial_state, reusable_query_context


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _turn_output(state: dict[str, Any]) -> dict[str, Any]:
    """Return only public, evaluator-relevant state instead of private traces."""
    return {
        "route_category": state.get("route_category"),
        "pipeline": state.get("pipeline", []),
        "is_valid": state.get("is_valid", False),
        "validation_error": state.get("validation_error"),
        "execution_error": state.get("execution_error"),
        "result_count": state.get("result_count", 0),
        "answer": state.get("answer", ""),
        "visualization": _json_value(state.get("visualization")),
    }


def run_evaluation_case(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute one isolated multi-turn case without persisting a conversation."""
    case_id = inputs["case_id"]
    case = CASES_BY_ID[case_id]
    conversation_id = f"evaluation-{case_id}-{uuid4()}"
    request_id = str(uuid4())
    chat_history: list[dict[str, str]] = []
    query_context: dict[str, Any] | None = None
    turn_outputs: list[dict[str, Any]] = []

    for turn_number, question in enumerate(case.turns, start=1):
        state = initial_state(
            question,
            chat_history=chat_history,
            query_context=query_context,
        )
        try:
            result = procurement_graph.invoke(
                state,
                config=agent_config(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    turn_id=f"evaluation-turn-{turn_number}",
                ),
            )
        except Exception as error:
            return {
                "case_id": case_id,
                "turns": turn_outputs,
                "error": f"{type(error).__name__}: {error}",
            }
        turn_outputs.append(_turn_output(result))
        chat_history.extend((
            {"role": "user", "content": question},
            {"role": "assistant", "content": result.get("answer", "")},
        ))
        query_context = reusable_query_context(result)

    return {"case_id": case_id, "turns": turn_outputs}
