from app.errors import state_error

from app.ai.agent.state import (
    ProcurementAgentState,
)


def handle_validation_failure(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    return {
        **state,
        "answer": (
            "I couldn't generate a valid database "
            "query for that procurement question. "
            "Please try rephrasing the question."
        ),
        "agent_error": state_error(
            "QUERY_VALIDATION_FAILED",
            "validate_query",
            "I couldn't generate a valid database query. Please try rephrasing your question.",
            True,
        ),
    }