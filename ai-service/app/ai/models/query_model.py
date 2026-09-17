import json
from typing import Any

from pydantic import BaseModel, Field


class MongoQuery(BaseModel):
    description: str = Field(
        description=(
            "Short explanation of what the MongoDB "
            "aggregation pipeline does."
        )
    )

    pipeline_json: str = Field(
        description=(
            "A JSON-encoded array containing the MongoDB aggregation pipeline. "
            "MongoDB operator names such as $match, $group, and $sort must be "
            "preserved exactly as JSON object keys."
        )
    )


def parse_pipeline(value: str) -> list[dict[str, Any]]:
    """Decode a tool result without trusting its MongoDB structure."""
    try:
        pipeline = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("The generated pipeline is not valid JSON.") from error

    if not isinstance(pipeline, list) or not all(
        isinstance(stage, dict) for stage in pipeline
    ):
        raise ValueError("The generated pipeline must be a JSON array of objects.")

    return pipeline
