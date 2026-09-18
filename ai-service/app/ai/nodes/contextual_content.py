import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.nodes.generate_answer import (
    clean_visualization_answer,
    requested_visualization_type,
)
from app.ai.prompts.contextual_content_prompt import (
    CONTEXTUAL_CONTENT_SYSTEM_PROMPT,
)


def contextual_content(
    state: ProcurementAgentState,
) -> ProcurementAgentState:
    """Answer from the prior result without generating or executing a query."""
    visualization_type = requested_visualization_type(state["question"])
    query_result = state.get("contextual_query_result", [])
    has_context = state.get("has_contextual_data", False)

    contextual_state = {
        **state,
        "pipeline": state.get("contextual_pipeline", []),
        "query_description": state.get("contextual_query_description", ""),
        "query_result": query_result,
        "result_count": state.get("contextual_result_count", len(query_result)),
        "execution_error": None,
        "visualization": None,
        "wants_visualization": visualization_type != "none",
        "visualization_type": visualization_type,
    }

    if not has_context:
        return {
            **contextual_state,
            "answer": (
                "I don't have a previous procurement result to reuse. Please "
                "ask for the analysis first, then request the format you want."
            ),
            "wants_visualization": False,
            "visualization_type": "none",
        }

    result_text = json.dumps(query_result, default=str, ensure_ascii=False)
    prompt = f"""
Current user request:
{state["question"]}

Previous query description:
{state.get("contextual_query_description", "")}

Reusable procurement result:
{result_text}
"""
    response = get_llm().invoke(
        [
            SystemMessage(content=CONTEXTUAL_CONTENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    answer = response.content
    if visualization_type != "none":
        answer = clean_visualization_answer(answer)

    return {**contextual_state, "answer": answer}
