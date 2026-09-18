from pymongo.errors import PyMongoError

from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.database.mongodb import (
    procurement_collection,
)


MAX_RETURNED_RESULTS = 100


def execute_query(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    # Never execute an invalid pipeline
    if not state.get("is_valid", False):
        return {
            **state,
            "query_result": [],
            "result_count": 0,
            "execution_error": (
                "Query was not executed because "
                "validation failed."
            ),
        }

    pipeline = state.get(
        "pipeline",
        []
    )

    # Make a copy so we do not modify
    # the LLM-generated pipeline stored in state.
    execution_pipeline = list(pipeline)

    # Safety net:
    # prevent huge result sets from being returned.
    has_limit = any(
        "$limit" in stage
        for stage in execution_pipeline
    )

    if not has_limit:
        execution_pipeline.append(
            {
                "$limit": MAX_RETURNED_RESULTS
            }
        )

    try:

        result = list(
            procurement_collection.aggregate(
                execution_pipeline,
                maxTimeMS=15_000,
            )
        )

        return {
            **state,
            "query_result": result,
            "result_count": len(result),
            "execution_error": None,
            "has_contextual_data": True,
            "contextual_query_result": result,
            "contextual_query_description": state.get("query_description", ""),
            "contextual_pipeline": state.get("pipeline", []),
            "contextual_result_count": len(result),
        }

    except PyMongoError as error:

        return {
            **state,
            "query_result": [],
            "result_count": 0,
            "execution_error": str(error),
        }
