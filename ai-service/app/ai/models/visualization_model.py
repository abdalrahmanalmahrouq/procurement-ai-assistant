from typing import Literal

from pydantic import BaseModel, Field

ValueFormat = Literal["currency", "number", "percent"]
VisualizationType = Literal[
    "bar",
    "line",
    "area",
    "pie",
    "donut",
    "metric",
]
VisualizationSelection = Literal[
    "bar",
    "line",
    "area",
    "pie",
    "donut",
    "metric",
    "none",
]


class VisualizationDatum(BaseModel):
    label: str = Field(description="A concise label for this data point.")
    value: float = Field(description="The numeric value for this data point.")


class Visualization(BaseModel):
    type: VisualizationType = Field(
        description="The predefined React visualization template to render."
    )
    title: str = Field(description="A short, informative visualization title.")
    subtitle: str = Field(
        description=(
            "Optional context such as a date range; use an empty string if absent."
        )
    )
    x_axis_label: str = Field(
        description="X-axis label, or an empty string when it is not applicable."
    )
    y_axis_label: str = Field(
        description="Y-axis label, or an empty string when it is not applicable."
    )
    value_format: ValueFormat = Field(
        description="How React should format the numeric values."
    )
    data: list[VisualizationDatum] = Field(
        description="Ordered data points derived only from the query result."
    )
