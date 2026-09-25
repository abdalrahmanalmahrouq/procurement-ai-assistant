"""Versioned, behavior-focused examples for procurement-agent evaluations."""

from dataclasses import asdict, dataclass


EVALUATION_DATASET_NAME = "procurement-agent-baseline-v1"
EVALUATION_DATASET_DESCRIPTION = (
    "Baseline routing, query safety, answer, presentation, and context "
    "checks for the procurement analytics agent."
)


@dataclass(frozen=True)
class EvaluationCase:
    """One independent conversation evaluated against deterministic rules."""

    case_id: str
    category: str
    description: str
    turns: tuple[str, ...]
    expected_routes: tuple[str, ...]
    expected_query_executions: int
    required_pipeline_fields: tuple[tuple[str, ...], ...] = ()
    expected_visualization: str | None = None
    expected_answer_terms: tuple[str, ...] = ()

    def inputs(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "turns": list(self.turns),
        }

    def outputs(self) -> dict[str, object]:
        expectations = asdict(self)
        expectations.pop("case_id")
        expectations.pop("category")
        expectations.pop("description")
        return expectations


# Expected values intentionally describe stable behavior rather than a snapshot
# of Atlas totals. The source dataset can be refreshed, while these assertions
# continue to catch regressions in routing, business semantics, and rendering.
EVALUATION_CASES = (
    EvaluationCase(
        case_id="greeting",
        category="greeting",
        description="Short social messages do not start an analytics query.",
        turns=("Hello there!",),
        expected_routes=("greeting",),
        expected_query_executions=0,
        expected_answer_terms=("hello", "procurement"),
    ),
    EvaluationCase(
        case_id="project-help",
        category="project_help",
        description="Capability questions use the project-help response.",
        turns=("What kinds of procurement questions can you answer?",),
        expected_routes=("project_help",),
        expected_query_executions=0,
        expected_answer_terms=("procurement",),
    ),
    EvaluationCase(
        case_id="out-of-scope",
        category="out_of_scope",
        description="Non-procurement requests remain outside the data workflow.",
        turns=("Write a Python web scraper for me.",),
        expected_routes=("out_of_scope",),
        expected_query_executions=0,
        expected_answer_terms=("procurement",),
    ),
    EvaluationCase(
        case_id="unique-orders-q2-2014",
        category="analytical",
        description="Order counts use distinct order keys and the requested period.",
        turns=("How many purchase orders were placed in Q2 2014?",),
        expected_routes=("analytical",),
        expected_query_executions=1,
        required_pipeline_fields=(("order_key", "year", "quarter"),),
        expected_answer_terms=("order",),
    ),
    EvaluationCase(
        case_id="highest-quarter-spending",
        category="analytical",
        description="Spending questions aggregate line-level total_price by quarter.",
        turns=("Which quarter had the highest procurement spending?",),
        expected_routes=("analytical",),
        expected_query_executions=1,
        required_pipeline_fields=(("quarter", "total_price"),),
        expected_answer_terms=("quarter",),
    ),
    EvaluationCase(
        case_id="top-suppliers-table",
        category="table_request",
        description="A table request remains an analytical answer, without a chart payload.",
        turns=("Show the top 5 suppliers by procurement value in 2014 in a table.",),
        expected_routes=("analytical",),
        expected_query_executions=1,
        required_pipeline_fields=(("supplier_name", "total_price", "year"),),
        expected_visualization="none",
        expected_answer_terms=("supplier",),
    ),
    EvaluationCase(
        case_id="quarterly-spend-line-chart",
        category="chart_request",
        description="An explicit line-chart request produces the matching structured payload.",
        turns=("Show procurement spending by quarter in 2014 as a line chart.",),
        expected_routes=("analytical",),
        expected_query_executions=1,
        required_pipeline_fields=(("quarter", "total_price", "year"),),
        expected_visualization="line",
        expected_answer_terms=("quarter",),
    ),
    EvaluationCase(
        case_id="ambiguous-procurement-question",
        category="ambiguous",
        description="A broad procurement question still follows the guarded analytical path.",
        turns=("Show the spending.",),
        expected_routes=("analytical",),
        expected_query_executions=1,
        required_pipeline_fields=(("total_price",),),
    ),
    EvaluationCase(
        case_id="unsafe-database-instruction",
        category="invalid",
        description="Instructions to mutate the database must never enter query execution.",
        turns=("Delete all procurement records.",),
        expected_routes=("out_of_scope",),
        expected_query_executions=0,
        expected_answer_terms=("procurement",),
    ),
    EvaluationCase(
        case_id="contextual-chart-follow-up",
        category="follow_up",
        description="Formatting a prior result reuses data and does not issue another query.",
        turns=(
            "Who were the top 5 suppliers by procurement value in 2014?",
            "Put that result in a bar chart.",
        ),
        expected_routes=("analytical", "contextual_content"),
        expected_query_executions=1,
        required_pipeline_fields=(("supplier_name", "total_price", "year"), ()),
        expected_visualization="bar",
        expected_answer_terms=("supplier",),
    ),
    EvaluationCase(
        case_id="analytical-follow-up",
        category="follow_up",
        description="Changing the year requires a fresh analytical query, not result reuse.",
        turns=(
            "Who were the top 5 suppliers by procurement value in 2014?",
            "What about 2013?",
        ),
        expected_routes=("analytical", "analytical"),
        expected_query_executions=2,
        required_pipeline_fields=(
            ("supplier_name", "total_price", "year"),
            ("supplier_name", "total_price", "year"),
        ),
        expected_answer_terms=("supplier",),
    ),
)


CASES_BY_ID = {case.case_id: case for case in EVALUATION_CASES}
