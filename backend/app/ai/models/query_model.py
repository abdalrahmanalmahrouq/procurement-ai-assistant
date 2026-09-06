from typing import Any

from pydantic import BaseModel, Field


class MongoQuery(BaseModel):
    description: str = Field(
        description=(
            "Short explanation of what the MongoDB "
            "aggregation pipeline does."
        )
    )

    pipeline: list[dict[str, Any]] = Field(
        description=(
            "MongoDB aggregation pipeline used to "
            "answer the user's question."
        )
    )