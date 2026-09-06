from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="User's procurement question."
    )

    conversation_id: str | None = Field(
        default=None,
        description=(
            "Conversation identifier used to "
            "preserve follow-up context."
        )
    )


class ChatResponse(BaseModel):
    conversation_id: str

    answer: str

    query_description: str | None = None

    pipeline: list[dict[str, Any]] | None = None

    result_count: int = 0

    retry_count: int = 0