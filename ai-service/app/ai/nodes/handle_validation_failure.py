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
    }