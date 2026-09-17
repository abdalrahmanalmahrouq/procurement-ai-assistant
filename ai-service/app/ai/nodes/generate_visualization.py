import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.models.visualization_model import Visualization
from app.ai.prompts.visualization_prompt import VISUALIZATION_SYSTEM_PROMPT


MAX_VISUALIZATION_ROWS = 20


def generate_visualization(
    state: ProcurementAgentState,
) -> ProcurementAgentState:
    """Create presentation-only JSON from an already executed query."""
    query_result = state.get("query_result", [])
    visualization_type = state.get("visualization_type", "none")

    if not query_result or visualization_type == "none":
        return {**state, "visualization": None}

    result_json = json.dumps(
        query_result[:MAX_VISUALIZATION_ROWS],
        default=str,
        ensure_ascii=False,
    )
    prompt = f"""
User question:
{state["question"]}

Requested visualization type:
{visualization_type}

Query description:
{state.get("query_description", "")}

MongoDB result:
{result_json}
"""

    visualization = (
        get_llm()
        .with_structured_output(
            Visualization,
            method="function_calling",
            strict=True,
        )
        .invoke(
            [
                SystemMessage(content=VISUALIZATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
    )

    # The router owns template selection; do not allow a later model call to
    # silently change a type the user requested.
    visualization.type = visualization_type
    visualization.data = visualization.data[:MAX_VISUALIZATION_ROWS]
    if visualization.type == "metric":
        visualization.data = visualization.data[:1]

    return {**state, "visualization": visualization}
