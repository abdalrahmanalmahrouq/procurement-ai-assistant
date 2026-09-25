"""Safe, correlated errors shared by the AI HTTP and streaming boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from pymongo.errors import PyMongoError


@dataclass
class ApplicationError(Exception):
    code: str
    stage: str
    message: str
    retryable: bool
    status_code: int = 500

    def payload(self, request_id: str, conversation_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request_id": request_id,
            "status": "error",
            "error": {
                "code": self.code,
                "stage": self.stage,
                "message": self.message,
                "retryable": self.retryable,
            },
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        return payload


def classify_error(error: Exception, stage: str = "agent") -> ApplicationError:
    """Translate provider and infrastructure details into a safe public error."""
    error_name = type(error).__name__.lower()
    error_text = str(error).lower()

    if isinstance(error, TimeoutError) or "timeout" in error_name or "timeout" in error_text:
        return ApplicationError(
            "MODEL_TIMEOUT" if stage in {"route_question", "generate_query", "correct_query", "generate_answer", "contextual_content", "generate_visualization"} else "REQUEST_TIMEOUT",
            stage,
            "The assistant took too long to respond. Please try again.",
            True,
            504,
        )

    if isinstance(error, PyMongoError):
        return ApplicationError(
            "DATABASE_UNAVAILABLE",
            "execute_query",
            "Procurement data is temporarily unavailable. Please try again.",
            True,
            503,
        )

    if any(token in error_name or token in error_text for token in ("api", "connection", "serviceunavailable", "authentication", "provider", "openrouter", "configured", "configuration")):
        return ApplicationError(
            "MODEL_UNAVAILABLE",
            stage,
            "The assistant service is temporarily unavailable. Please try again.",
            True,
            503,
        )

    if isinstance(error, (ValidationError, ValueError)) and stage in {
        "route_question",
        "generate_query",
        "correct_query",
        "generate_visualization",
    }:
        return ApplicationError(
            "MODEL_OUTPUT_INVALID",
            stage,
            "The assistant returned an invalid response. Please try again.",
            True,
            502,
        )

    return ApplicationError(
        "INTERNAL_ERROR",
        stage,
        "The assistant could not complete this request. Please try again.",
        True,
        500,
    )


def state_error(
    code: str,
    stage: str,
    message: str,
    retryable: bool,
) -> dict[str, Any]:
    """Store a controlled graph failure without leaking implementation details."""
    return {
        "code": code,
        "stage": stage,
        "message": message,
        "retryable": retryable,
    }
