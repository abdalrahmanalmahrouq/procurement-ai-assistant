from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.models.query_model import MongoQuery, parse_pipeline
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
        MongoQuery,
        method="function_calling",
        strict=True,
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

    try:
        pipeline = parse_pipeline(result.pipeline_json)
    except ValueError:
        # Let the deterministic validator route malformed model output through
        # the normal correction path instead of crashing the whole request.
        pipeline = []

    return {
        **state,
        "pipeline": pipeline,
        "query_description": result.description,
        # A newly requested analysis supersedes the previous result. The
        # execute node will install fresh reusable context after success.
        "has_contextual_data": False,
        "contextual_query_result": [],
        "contextual_query_description": "",
        "contextual_pipeline": [],
        "contextual_result_count": 0,
    }
