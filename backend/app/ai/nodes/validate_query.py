from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.ai.validators.mongo_validator import (
    validate_pipeline,
)


def validate_query(
    state: ProcurementAgentState
) -> ProcurementAgentState:

    pipeline = state.get(
        "pipeline",
        []
    )

    is_valid, error = validate_pipeline(
        pipeline
    )

    return {
        **state,
        "is_valid": is_valid,
        "validation_error": error,
    }