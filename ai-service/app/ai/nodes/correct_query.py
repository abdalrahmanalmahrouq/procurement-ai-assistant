from pprint import pformat

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.ai.llm import get_llm

from app.ai.models.query_model import (
    MongoQuery,
    parse_pipeline,
)

from app.ai.prompts.query_prompt import (
    QUERY_GENERATION_SYSTEM_PROMPT,
)


def correct_query(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        MongoQuery,
        method="function_calling",
        strict=True,
    )

    question = state["question"]

    invalid_pipeline = state.get(
        "pipeline",
        []
    )

    validation_error = state.get(
        "validation_error",
        "Unknown validation error"
    )

    retry_count = state.get(
        "retry_count",
        0
    )

    correction_prompt = f"""
The MongoDB aggregation pipeline you generated
for the user's question failed validation.

USER QUESTION:
{question}

INVALID PIPELINE:
{pformat(invalid_pipeline)}

VALIDATION ERROR:
{validation_error}

Generate a corrected MongoDB aggregation pipeline.

Important:
- Fix the validation error.
- Still answer the original user question.
- Follow all procurement schema and MongoDB rules
  from the system prompt.
- Do not change the meaning of the user's question.
"""

    result = structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    QUERY_GENERATION_SYSTEM_PROMPT
                )
            ),
            HumanMessage(
                content=correction_prompt
            ),
        ]
    )

    try:
        pipeline = parse_pipeline(result.pipeline_json)
    except ValueError:
        pipeline = []

    return {
        **state,

        "pipeline":
            pipeline,

        "query_description":
            result.description,

        "retry_count":
            retry_count + 1,

        # Reset previous validation state
        "is_valid":
            False,

        "validation_error":
            None,
    }
