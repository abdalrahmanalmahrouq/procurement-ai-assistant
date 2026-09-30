"""A separate report workflow; ordinary analytical answers never enter it."""

import json
import re
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.ai.agent.state import ProcurementAgentState
from app.ai.llm import get_llm
from app.ai.models.report_planning import PLAN_PROMPT, WRITE_PROMPT
from app.ai.nodes.execute_query import execute_query
from app.ai.nodes.generate_query import generate_query
from app.ai.validators.mongo_validator import validate_pipeline
from app.models.report import ReportNarrative, ReportSpec
from app.services.report_service import (
    gather_standard_data, report_match, render_report_artifact,
    save_rendered_report, validate_report,
)


def plan_report(state: ProcurementAgentState) -> dict:
    if state.get("report_spec_input"):
        spec = ReportSpec.model_validate(state["report_spec_input"])
    else:
        spec = get_llm().with_structured_output(
            ReportSpec, method="function_calling", strict=True,
        ).invoke([SystemMessage(content=PLAN_PROMPT), HumanMessage(content=state["question"])])
        spec = ReportSpec.model_validate(spec)
        period_mentioned = re.search(
            r"\b(?:20\d{2}|this year|current year|last year|this quarter|last quarter)\b",
            state["question"],
            re.IGNORECASE,
        )
        planned = spec.model_dump()
        if not period_mentioned:
            planned.update({
                "report_type": "all",
                "year": None,
                "quarter": None,
                "sections": [
                    section for section in spec.sections
                    if section != "category_comparison"
                ],
            })
        acquisition = re.search(
            r"\b(?:NON-IT Goods|IT Goods)\b",
            state["question"],
            re.IGNORECASE,
        )
        if acquisition:
            value = (
                "NON-IT Goods"
                if acquisition.group().lower().startswith("non") else "IT Goods"
            )
            planned["acquisition_type"] = value
            if not re.search(r"\b(?:category|commodity)\b", state["question"], re.IGNORECASE):
                planned["category"] = None
        if (
            re.search(r"\bdepartments?\b", state["question"], re.IGNORECASE)
            and re.search(r"\bquarters?\b", state["question"], re.IGNORECASE)
            and re.search(r"\b(?:five|5|top|highest)\b", state["question"], re.IGNORECASE)
        ):
            planned["report_focus"] = "department"
            if not re.search(r"\bdepartment (?:of|named)\b", state["question"], re.IGNORECASE):
                planned["department"] = None
            if "department_quarterly" not in planned["sections"]:
                planned["sections"].append("department_quarterly")
            if re.search(r"\b(?:five|5)\b", state["question"], re.IGNORECASE):
                planned["ranking_limit"] = 5
        spec = ReportSpec.model_validate(planned)
    return {"report_spec": spec.model_dump(mode="json")}


def gather_report_data(state: ProcurementAgentState) -> dict:
    spec = ReportSpec.model_validate(state["report_spec"])
    data = gather_standard_data(spec)
    if "custom_analysis" in spec.sections:
        data["custom_analysis"] = []
        for requirement in spec.custom_requirements:
            scoped_question = (
                f"{requirement}. Restrict records to {json.dumps(report_match(spec))}. "
                "Spending is sum(total_price); orders are distinct order_key. "
                "Return at most 50 rows."
            )
            generated = generate_query({"question": scoped_question, "chat_history": []})
            pipeline = generated.get("pipeline", [])
            valid, reason = validate_pipeline(pipeline)
            if not valid:
                raise ValueError(f"Custom analysis query was invalid: {reason}")
            # An initial match enforces the same scope even if the model
            # omitted or contradicted the requested filters.
            scoped_pipeline = [{"$match": report_match(spec)}, *pipeline]
            valid, reason = validate_pipeline(scoped_pipeline)
            if not valid:
                raise ValueError(f"Custom analysis query was invalid: {reason}")
            result = execute_query({"is_valid": True, "pipeline": scoped_pipeline})
            if result.get("execution_error"):
                raise ValueError("Custom analysis could not retrieve data.")
            data["custom_analysis"].extend({**row, "requirement": requirement} for row in result.get("query_result", []))
    return {"report_data": data}


def generate_report(state: ProcurementAgentState) -> dict:
    spec = ReportSpec.model_validate(state["report_spec"])
    data = state["report_data"]
    narrative = get_llm().with_structured_output(
        ReportNarrative, method="function_calling", strict=True,
    ).invoke([
        SystemMessage(content=WRITE_PROMPT),
        HumanMessage(content=json.dumps({"spec": spec.model_dump(mode="json"), "verified_data": data}, default=str)),
    ])
    return {"report_narrative": ReportNarrative.model_validate(narrative).model_dump()}


def validate_report_node(state: ProcurementAgentState) -> dict:
    spec = ReportSpec.model_validate(state["report_spec"])
    narrative = ReportNarrative.model_validate(state["report_narrative"])
    validate_report(spec, state["report_data"], narrative)
    return {"report_valid": True}


def render_report(state: ProcurementAgentState) -> dict:
    report_id = str(uuid4())
    render_report_artifact(
        ReportSpec.model_validate(state["report_spec"]),
        state["report_data"],
        ReportNarrative.model_validate(state["report_narrative"]),
        report_id,
    )
    return {"report_id": report_id}


def save_report_node(state: ProcurementAgentState) -> dict:
    report = save_rendered_report(
        ReportSpec.model_validate(state["report_spec"]),
        state["report_data"],
        ReportNarrative.model_validate(state["report_narrative"]),
        state.get("conversation_id"),
        state.get("request_id", ""),
        state["report_id"],
    )
    return {"report": report, "answer": f"Your {report['title']} is ready. Open the report to review the verified data, charts, and tables, or download its PDF and CSV exports."}


def build_report_graph():
    builder = StateGraph(ProcurementAgentState)
    for name, node in (
        ("plan_report", plan_report),
        ("gather_report_data", gather_report_data),
        ("generate_report", generate_report),
        ("validate_report_content", validate_report_node),
        ("render_report", render_report),
        ("save_report", save_report_node),
    ):
        builder.add_node(name, node)
    builder.add_edge(START, "plan_report")
    builder.add_edge("plan_report", "gather_report_data")
    builder.add_edge("gather_report_data", "generate_report")
    builder.add_edge("generate_report", "validate_report_content")
    builder.add_edge("validate_report_content", "render_report")
    builder.add_edge("render_report", "save_report")
    builder.add_edge("save_report", END)
    return builder.compile()


report_graph = build_report_graph()
