from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.models.query_model import MongoQuery
from app.ai.prompts.query_prompt import (
    QUERY_GENERATION_SYSTEM_PROMPT,
)

def build_history_messages(
    chat_history: list[dict[str, str]]
):
    messages = []

    for message in chat_history:

        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            messages.append(
                HumanMessage(content=content)
            )

        elif role == "assistant":
            messages.append(
                AIMessage(content=content)
            )

    return messages

def generate_query(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        MongoQuery
    )

    question = state["question"]

    chat_history = state.get(
        "chat_history",
        []
    )

    messages = [
        SystemMessage(
            content=QUERY_GENERATION_SYSTEM_PROMPT
        )
    ]

    messages.extend(
        build_history_messages(
            chat_history
        )
    )

    messages.append(
        HumanMessage(
            content=question
        )
    )

    result = structured_llm.invoke(
        messages
    )

    return {
        **state,
        "pipeline": result.pipeline,
        "query_description": result.description,
    }