import json

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.ai.llm import get_llm

from app.ai.prompts.answer_prompt import (
    ANSWER_GENERATION_SYSTEM_PROMPT,
)


def generate_answer(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    # ----------------------------------
    # Handle execution failures
    # ----------------------------------

    if state.get("execution_error"):

        return {
            **state,
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
            **state,
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

    return {
        **state,
        "answer": response.content
    }