from typing import Literal

from pydantic import BaseModel, Field


RouteCategory = Literal[
    "greeting",
    "project_help",
    "out_of_scope",
    "analytical",
]


class RouteDecision(BaseModel):
    route: RouteCategory = Field(
        description=(
            "The workflow branch that should handle the user's message."
        )
    )
