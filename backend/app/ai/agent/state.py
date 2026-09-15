from typing import Any, TypedDict

from app.ai.models.route_model import RouteCategory


class ProcurementAgentState(TypedDict, total=False):

    # User input
    question: str

    # Initial intent routing
    route_category: RouteCategory

    # Previous conversation context
    chat_history: list[dict[str, str]]

    # Generated MongoDB aggregation
    pipeline: list[dict[str, Any]]

    # Human-readable reasoning/description
    query_description: str

    # Validation
    is_valid: bool
    validation_error: str | None

    # MongoDB result
    query_result: list[dict[str, Any]]
    result_count: int

    execution_error: str | None
    
    # Final response
    answer: str

    # Retry handling
    retry_count: int
