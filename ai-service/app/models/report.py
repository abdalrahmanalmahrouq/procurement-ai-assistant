from typing import Literal

from pydantic import BaseModel, Field, model_validator


ReportSection = Literal[
    "spending_overview", "order_statistics", "top_suppliers",
    "department_spending", "department_quarterly", "monthly_trends", "quarterly_trends",
    "category_spending", "category_comparison", "custom_analysis",
]

DEFAULT_SECTIONS: list[ReportSection] = [
    "spending_overview", "order_statistics", "top_suppliers",
    "department_spending", "monthly_trends", "quarterly_trends",
    "category_spending",
]


class ReportSpec(BaseModel):
    report_focus: Literal["comprehensive", "supplier", "department", "category"] = "comprehensive"
    report_type: Literal["all", "annual", "quarterly"] = "annual"
    year: int | None = Field(default=None, ge=2000, le=2100)
    quarter: int | None = Field(default=None, ge=1, le=4)
    department: str | None = Field(default=None, max_length=200)
    acquisition_type: str | None = Field(default=None, max_length=200)
    supplier: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=200)
    sections: list[ReportSection] = Field(default_factory=lambda: DEFAULT_SECTIONS.copy(), min_length=1)
    ranking_limit: int = Field(default=10, ge=1, le=50)
    charts: list[Literal["supplier", "department", "monthly", "quarterly", "category"]] = Field(default_factory=lambda: ["supplier", "department", "monthly"])
    tables: list[Literal["supplier", "department", "monthly", "quarterly", "category"]] = Field(default_factory=lambda: ["supplier", "department", "monthly", "quarterly", "category"])
    export_format: Literal["pdf", "pdf_csv"] = "pdf_csv"
    custom_requirements: list[str] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def validate_period_and_sections(self):
        if self.report_type in {"annual", "quarterly"} and self.year is None:
            raise ValueError("An annual or quarterly report requires a year.")
        if self.report_type == "quarterly" and self.quarter is None:
            raise ValueError("A quarterly report requires a quarter.")
        if self.report_type != "quarterly" and self.quarter is not None:
            raise ValueError("Only a quarterly report can specify a quarter.")
        if self.report_type == "all" and self.year is not None:
            raise ValueError("An all-years report cannot specify a year.")
        if self.report_type == "all" and "category_comparison" in self.sections:
            raise ValueError("Category comparison requires an annual or quarterly period.")
        if len(set(self.sections)) != len(self.sections):
            raise ValueError("Report sections must be unique.")
        if "custom_analysis" in self.sections and not self.custom_requirements:
            raise ValueError("Custom analysis requires a question.")
        if self.custom_requirements and "custom_analysis" not in self.sections:
            raise ValueError("Custom requirements need the custom_analysis section.")
        return self


class ReportNarrative(BaseModel):
    executive_summary: str
    spending_overview: str
    supplier_analysis: str
    department_analysis: str
    spending_trends: str
    key_observations: str
    conclusion: str
