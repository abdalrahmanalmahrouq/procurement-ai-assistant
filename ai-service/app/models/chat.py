from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.ai.models.visualization_model import Visualization


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="User's procurement question."
    )

    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description=(
            "Conversation identifier used to "
            "preserve follow-up context."
        )
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Please enter a question.")
        return value


class ChatResponse(BaseModel):
    conversation_id: str

    answer: str

    query_description: str | None = None

    pipeline: list[dict[str, Any]] | None = None

    result_count: int = 0

    retry_count: int = 0

    visualization: Visualization | None = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class StoredMessage(BaseModel):
    id: str
    conversation_id: str
    turn_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    query_description: str | None = None
    pipeline: list[dict[str, Any]] | None = None
    result_count: int = 0
    retry_count: int = 0
    visualization: Visualization | None = None
    status: Literal["pending", "complete", "error"] = "complete"


class ConversationMessages(BaseModel):
    conversation: ConversationSummary
    messages: list[StoredMessage]
