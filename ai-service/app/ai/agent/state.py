from typing import Any, TypedDict

from app.ai.models.route_model import RouteCategory
from app.ai.models.visualization_model import Visualization, VisualizationSelection


class ProcurementAgentState(TypedDict, total=False):

    # User input
    question: str

    # Initial intent routing
    route_category: RouteCategory
    wants_visualization: bool
    visualization_type: VisualizationSelection

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

    # Most recent successfully executed result. These fields are kept
    # separately so a contextual follow-up can reuse the data without
    # pretending that it generated or executed a new query.
    has_contextual_data: bool
    contextual_query_result: list[dict[str, Any]]
    contextual_query_description: str
    contextual_pipeline: list[dict[str, Any]]
    contextual_result_count: int

    # Optional presentation generated from the query result
    visualization: Visualization | None

    # Final response
    answer: str

    # Retry handling
    retry_count: int
