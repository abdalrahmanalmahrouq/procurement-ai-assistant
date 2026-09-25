import re

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.models.route_model import RouteDecision
from app.ai.prompts.route_prompt import ROUTE_SYSTEM_PROMPT


MUTATING_DATABASE_INSTRUCTION = re.compile(
    r"\b(delete|drop|truncate|erase|wipe|remove|update|insert|modify)\b"
    r"[\s\S]{0,80}\b(record|records|collection|collections|database|data)\b",
    flags=re.IGNORECASE,
)


def requests_database_mutation(question: str) -> bool:
    """Keep mutation requests out of the LLM-driven analytics workflow."""
    return bool(MUTATING_DATABASE_INSTRUCTION.search(question))


def route_question(
    state: ProcurementAgentState,
) -> ProcurementAgentState:
    """Classify a turn before any query-generation work is performed."""
    if requests_database_mutation(state["question"]):
        return {**state, "route_category": "out_of_scope"}

    messages = [SystemMessage(content=ROUTE_SYSTEM_PROMPT)]

    if state.get("has_contextual_data", False):
        messages.append(SystemMessage(content=(
            "A reusable result from the most recent successful procurement "
            "query is available for contextual_content requests."
        )))
    else:
        messages.append(SystemMessage(content=(
            "No reusable procurement query result is available. Do not choose "
            "contextual_content; choose analytical if procurement data is needed."
        )))

    for message in state.get("chat_history", []):
        content = message.get("content", "")
        if message.get("role") == "user":
            messages.append(HumanMessage(content=content))
        elif message.get("role") == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=state["question"]))

    result = (
        get_llm()
        .with_structured_output(
            RouteDecision,
            method="function_calling",
            strict=True,
        )
        .invoke(messages)
    )

    return {
        **state,
        "route_category": result.route,
    }
