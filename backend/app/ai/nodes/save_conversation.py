from app.ai.agent.state import (
    ProcurementAgentState,
)


def save_conversation(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    history = list(
        state.get(
            "chat_history",
            []
        )
    )

    question = state.get(
        "question",
        ""
    )

    answer = state.get(
        "answer",
        ""
    )

    if question:
        history.append({
            "role": "user",
            "content": question
        })

    if answer:
        history.append({
            "role": "assistant",
            "content": answer
        })

    return {
        **state,
        "chat_history": history,
    }