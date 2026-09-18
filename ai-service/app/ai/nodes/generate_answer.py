import json
import re

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.ai.llm import get_llm
from app.ai.models.visualization_model import VisualizationSelection

from app.ai.prompts.answer_prompt import (
    ANSWER_GENERATION_SYSTEM_PROMPT,
)


VISUALIZATION_TERMS = (
    "chart",
    "graph",
    "plot",
    "visualize",
    "visualise",
    "visualization",
    "visualisation",
    "metric card",
    "kpi",
)

NAMED_VISUALIZATION_TYPES = (
    ("bar", ("bar chart", "bar graph", "column chart")),
    ("line", ("line chart", "line graph")),
    ("area", ("area chart", "area graph")),
    ("pie", ("pie chart", "pie graph")),
    ("donut", ("donut chart", "doughnut chart")),
    ("metric", ("metric card", "kpi card", "kpi")),
)

FENCED_BLOCK_PATTERN = re.compile(
    r"```[^\n]*\n?[\s\S]*?(?:```|$)",
    flags=re.IGNORECASE,
)


def _contains_term(text: str, terms: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"\b{re.escape(term)}\b", text)
        for term in terms
    )


def requested_visualization_type(question: str) -> VisualizationSelection:
    """Detect an explicit visualization request and choose its template."""
    question = question.lower()
    if not _contains_term(question, VISUALIZATION_TERMS):
        return "none"

    for visualization_type, phrases in NAMED_VISUALIZATION_TYPES:
        if any(phrase in question for phrase in phrases):
            return visualization_type

    if _contains_term(question, ("cumulative", "running total")):
        return "area"
    if _contains_term(
        question,
        ("trend", "timeline", "year", "quarter", "month", "date"),
    ):
        return "line"
    if _contains_term(
        question,
        ("share", "breakdown", "proportion", "percentage", "distribution"),
    ):
        return "donut"
    if _contains_term(question, ("total", "count", "number", "metric", "kpi")):
        return "metric"

    return "bar"


def clean_visualization_answer(answer: str) -> str:
    """Remove model-generated diagrams duplicated by the React visualization."""
    cleaned = FENCED_BLOCK_PATTERN.sub("", answer).strip()
    return cleaned or "Here is the requested visualization."


def generate_answer(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    visualization_type = requested_visualization_type(state["question"])
    answer_state = {
        **state,
        "wants_visualization": visualization_type != "none",
        "visualization_type": visualization_type,
    }

    # ----------------------------------
    # Handle execution failures
    # ----------------------------------

    if state.get("execution_error"):

        return {
            **answer_state,
            "answer": (
                "I was unable to retrieve the "
                "procurement data needed to answer "
                "that question."
            )
        }

    question = state["question"]

    query_result = state.get(
        "query_result",
        []
    )

    query_description = state.get(
        "query_description",
        ""
    )

    # ----------------------------------
    # Handle empty results
    # ----------------------------------

    if not query_result:

        return {
            **answer_state,
            "answer": (
                "No matching procurement records "
                "were found for that query."
            )
        }

    llm = get_llm()

    result_text = json.dumps(
        query_result,
        default=str,
        ensure_ascii=False
    )

    prompt = f"""
User question:
{question}

Query description:
{query_description}

MongoDB result:
{result_text}

Answer the user's procurement question using only
the result above.
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    ANSWER_GENERATION_SYSTEM_PROMPT
                )
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    answer = response.content
    if visualization_type != "none":
        answer = clean_visualization_answer(answer)

    return {
        **answer_state,
        "answer": answer
    }
