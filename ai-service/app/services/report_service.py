"""Verified report data, deterministic exports, and durable report metadata."""

import csv
import io
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String

from app.ai.nodes.execute_query import normalize_mongo_value
from app.database.mongodb import procurement_collection, reports_collection
from app.models.report import ReportSpec, ReportNarrative


REPORT_DIR = Path(
    os.getenv(
        "REPORT_STORAGE_DIR",
        str(Path(__file__).resolve().parents[2] / "report_files"),
    )
)
SOURCE = "California Public Procurement Dataset; procurement_records"


def period_label(spec: ReportSpec) -> str:
    if spec.report_type == "all":
        return "All available years"
    return f"{spec.year} Q{spec.quarter}" if spec.quarter else str(spec.year)


def report_title(spec: ReportSpec) -> str:
    focus = "" if spec.report_focus == "comprehensive" else f"{spec.report_focus.title()} "
    return f"{period_label(spec)} {focus}Procurement Report"


def report_match(spec: ReportSpec, *, comparison=False) -> dict:
    match = {}
    if spec.year is not None:
        match["year"] = spec.year - 1 if comparison else spec.year
    if spec.quarter:
        match["quarter"] = spec.quarter
    if spec.department:
        match["department_name"] = spec.department
    if spec.acquisition_type:
        match["acquisition_type"] = spec.acquisition_type
    if spec.supplier:
        match["$or"] = [
            {"supplier_code": spec.supplier},
            {"supplier_name": spec.supplier},
        ]
    if spec.category:
        match["commodity_title"] = spec.category
    return match


def aggregate(match: dict, stages: list[dict]) -> list[dict]:
    return normalize_mongo_value(list(procurement_collection.aggregate(
        [{"$match": match}, *stages], allowDiskUse=True, maxTimeMS=30_000,
    )))


def overview(match: dict) -> dict:
    rows = aggregate(match, [
        {"$group": {"_id": "$order_key", "order_value": {"$sum": {"$ifNull": ["$total_price", 0]}}, "line_records": {"$sum": 1}}},
        {"$group": {"_id": None, "total_spending": {"$sum": "$order_value"}, "order_count": {"$sum": 1}, "line_records": {"$sum": "$line_records"}, "average_order_value": {"$avg": "$order_value"}}},
        {"$project": {"_id": 0}},
    ])
    result = rows[0] if rows else {}
    return {
        "total_spending": float(result.get("total_spending") or 0),
        "order_count": int(result.get("order_count") or 0),
        "line_records": int(result.get("line_records") or 0),
        "average_order_value": float(result.get("average_order_value") or 0),
    }


def ranking(match: dict, field: str, label: str, limit: int) -> list[dict]:
    if field == "supplier_name":
        identity = {"$cond": [{"$and": [{"$ne": ["$supplier_code", None]}, {"$ne": ["$supplier_code", ""]}]}, "$supplier_code", "$supplier_name"]}
    else:
        identity = f"${field}"
    ranked_match = dict(match)
    if field not in ranked_match:
        ranked_match[field] = {"$nin": [None, ""]}
    rows = aggregate(ranked_match, [
        {"$group": {"_id": {"entity": identity, "order": "$order_key"}, "name": {"$first": f"${field}"}, "order_value": {"$sum": {"$ifNull": ["$total_price", 0]}}, "line_records": {"$sum": 1}}},
        {"$group": {"_id": "$_id.entity", "name": {"$first": "$name"}, "total_spending": {"$sum": "$order_value"}, "order_count": {"$sum": 1}, "line_records": {"$sum": "$line_records"}}},
        {"$sort": {"total_spending": -1, "name": 1}},
        {"$limit": limit},
        {"$project": {"_id": 0, label: "$name", "total_spending": 1, "order_count": 1, "line_records": 1}},
    ])
    for row in rows:
        row["total_spending"] = float(row["total_spending"])
    return rows


def trend(match: dict, unit: str, include_year: bool = False) -> list[dict]:
    first_id = {"period": f"${unit}", "order": "$order_key"}
    if include_year:
        first_id["year"] = "$year"
    second_id = (
        {"year": "$_id.year", "period": "$_id.period"}
        if include_year else "$_id.period"
    )
    projection = {
        "_id": 0,
        unit: "$_id.period" if include_year else "$_id",
        "total_spending": 1,
        "order_count": 1,
    }
    if include_year:
        projection["year"] = "$_id.year"
    rows = aggregate(match, [
        {"$group": {
            "_id": first_id,
            "order_value": {"$sum": {"$ifNull": ["$total_price", 0]}},
        }},
        {"$group": {
            "_id": second_id,
            "total_spending": {"$sum": "$order_value"},
            "order_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
        {"$project": projection},
    ])
    for row in rows:
        row["total_spending"] = float(row["total_spending"])
        if include_year:
            period = f"{row['year']}-{int(row[unit]):02d}" if unit == "month" else f"{row['year']} Q{row[unit]}"
            row[unit] = period
    return rows


def department_quarterly(match: dict, limit: int) -> list[dict]:
    leaders = ranking(match, "department_name", "department", limit)
    if not leaders:
        return []
    department_match = {
        **match,
        "department_name": {"$in": [row["department"] for row in leaders]},
    }
    rows = aggregate(department_match, [
        {"$group": {
            "_id": {
                "department": "$department_name",
                "year": "$year",
                "quarter": "$quarter",
                "order": "$order_key",
            },
            "order_value": {"$sum": {"$ifNull": ["$total_price", 0]}},
        }},
        {"$group": {
            "_id": {
                "department": "$_id.department",
                "year": "$_id.year",
                "quarter": "$_id.quarter",
            },
            "total_spending": {"$sum": "$order_value"},
            "order_count": {"$sum": 1},
        }},
        {"$sort": {"_id.year": 1, "_id.quarter": 1, "_id.department": 1}},
        {"$project": {
            "_id": 0,
            "department": "$_id.department",
            "year": "$_id.year",
            "quarter": "$_id.quarter",
            "total_spending": 1,
            "order_count": 1,
        }},
    ])
    for row in rows:
        row["total_spending"] = float(row["total_spending"])
        row["department_period"] = (
            f"{row['department']} · {row['year']} Q{row['quarter']}"
        )
    return rows


def gather_standard_data(spec: ReportSpec) -> dict:
    match = report_match(spec)
    current = overview(match)
    previous = (
        overview(report_match(spec, comparison=True))
        if spec.year is not None else None
    )
    change = None
    if previous and previous["order_count"] and previous["total_spending"]:
        change = round(
            100 * (current["total_spending"] - previous["total_spending"])
            / previous["total_spending"], 2,
        )
    data = {
        "overview": current,
        "comparison": {
            "period": (
                f"{spec.year - 1}" + (f" Q{spec.quarter}" if spec.quarter else "")
                if spec.year is not None else "Not applicable"
            ),
            "total_spending": (
                previous["total_spending"]
                if previous and previous["order_count"] else None
            ),
            "change_percent": change,
        },
    }
    if "top_suppliers" in spec.sections:
        data["top_suppliers"] = ranking(match, "supplier_name", "supplier", spec.ranking_limit)
    if "department_spending" in spec.sections:
        data["department_spending"] = ranking(match, "department_name", "department", spec.ranking_limit)
    if "category_spending" in spec.sections:
        data["category_spending"] = ranking(match, "commodity_title", "category", spec.ranking_limit)
    if "category_comparison" in spec.sections:
        current_categories = ranking(match, "commodity_title", "category", spec.ranking_limit)
        previous_categories = ranking(report_match(spec, comparison=True), "commodity_title", "category", spec.ranking_limit)
        current_by_name = {row["category"]: row for row in current_categories}
        previous_by_name = {row["category"]: row for row in previous_categories}
        comparisons = []
        for name in current_by_name.keys() | previous_by_name.keys():
            current_value = current_by_name.get(name, {}).get("total_spending", 0)
            prior = previous_by_name.get(name)
            prior_value = prior["total_spending"] if prior else None
            comparisons.append({
                "category": name,
                "total_spending": current_value,
                "prior_spending": prior_value,
                "change_percent": (
                    round(100 * (current_value - prior_value) / prior_value, 2)
                    if prior_value else None
                ),
            })
        data["category_comparison"] = sorted(comparisons, key=lambda row: (-row["total_spending"], row["category"]))
    if "department_quarterly" in spec.sections:
        data["department_quarterly"] = department_quarterly(match, spec.ranking_limit)
    if "monthly_trends" in spec.sections:
        data["monthly_trends"] = trend(match, "month", spec.report_type == "all")
    if "quarterly_trends" in spec.sections:
        data["quarterly_trends"] = trend(match, "quarter", spec.report_type == "all")
    for key in ("top_suppliers", "department_spending", "category_spending"):
        for row in data.get(key, []):
            row["share_percent"] = round(100 * row["total_spending"] / current["total_spending"], 2) if current["total_spending"] else 0
    return data


def validate_report(spec: ReportSpec, data: dict, narrative: ReportNarrative) -> None:
    overview_data = data.get("overview")
    required_metrics = {
        "total_spending", "order_count", "line_records", "average_order_value"
    }
    if (
        not isinstance(overview_data, dict)
        or not required_metrics <= overview_data.keys()
        or any(not isinstance(overview_data[key], (int, float)) for key in required_metrics)
        or overview_data["order_count"] < 0
    ):
        raise ValueError("Report data is missing or invalid.")
    comparison = data.get("comparison")
    if (
        not isinstance(comparison, dict)
        or not {"period", "total_spending", "change_percent"} <= comparison.keys()
        or not isinstance(comparison["period"], str)
        or (
            comparison["total_spending"] is not None
            and not isinstance(comparison["total_spending"], (int, float))
        )
        or (
            comparison["change_percent"] is not None
            and not isinstance(comparison["change_percent"], (int, float))
        )
    ):
        raise ValueError("Report comparison data is missing or invalid.")
    required_columns = {
        "top_suppliers": {"supplier", "total_spending", "order_count", "share_percent"},
        "department_spending": {"department", "total_spending", "order_count", "share_percent"},
        "department_quarterly": {
            "department", "year", "quarter", "total_spending", "order_count"
        },
        "monthly_trends": {"month", "total_spending", "order_count"},
        "quarterly_trends": {"quarter", "total_spending", "order_count"},
        "category_spending": {"category", "total_spending", "order_count", "share_percent"},
        "category_comparison": {"category", "total_spending", "prior_spending", "change_percent"},
        "custom_analysis": {"requirement"},
    }
    for section in spec.sections:
        if section not in required_columns:
            continue
        rows = data.get(section)
        if not isinstance(rows, list):
            raise ValueError(f"Report section {section} is missing.")
        if any(not isinstance(row, dict) or not required_columns[section] <= row.keys() for row in rows):
            raise ValueError(f"Report section {section} has invalid table rows.")
        if section != "custom_analysis" and any(
            not isinstance(row["total_spending"], (int, float)) for row in rows
        ):
            raise ValueError(f"Report section {section} has invalid financial values.")
    for text in narrative.model_dump().values():
        if not text.strip() or any(character.isdigit() for character in text):
            raise ValueError("Report narrative is empty or contains unverified numbers.")


def money(value: float) -> str:
    return f"${value:,.2f}"


def chart(rows: list[dict], label_key: str, title: str) -> Drawing:
    values = rows[:16]
    height = 45 + len(values) * 18
    drawing = Drawing(510, height)
    drawing.add(String(
        4, height - 15, title, fontName="Helvetica-Bold",
        fontSize=10, fillColor=colors.HexColor("#102a43"),
    ))
    maximum = max((row.get("total_spending", 0) for row in values), default=0) or 1
    for index, row in enumerate(values):
        y = height - 37 - index * 18
        name = str(row.get(label_key, ""))[:27]
        drawing.add(String(4, y, name, fontSize=7, fillColor=colors.HexColor("#334155")))
        drawing.add(Rect(160, y - 2, max(0, 260 * row.get("total_spending", 0) / maximum), 9, fillColor=colors.HexColor("#16806a"), strokeColor=None))
        drawing.add(String(430, y, money(row.get("total_spending", 0)), fontSize=7, fillColor=colors.HexColor("#334155")))
    return drawing


def render_pdf(report: dict, destination: Path) -> None:
    spec = ReportSpec.model_validate(report["spec"])
    data = report["data"]
    narrative = ReportNarrative.model_validate(report["narrative"])
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#102a43")
    story = [
        Paragraph(escape(report["title"]), styles["Title"]),
        Paragraph(f"Reporting period: {escape(report['period'])}", styles["Heading2"]),
        Paragraph("California Public Procurement Dataset", styles["Normal"]),
        Spacer(1, 0.35 * inch),
        Paragraph("Executive summary", styles["Heading1"]),
        Paragraph(escape(narrative.executive_summary), styles["BodyText"]),
        Spacer(1, 0.15 * inch),
    ]
    metrics = data["overview"]
    metric_rows = [
        ["Total spending", "Unique orders", "Line records", "Average order value"],
        [
            money(metrics["total_spending"]),
            str(metrics["order_count"]),
            str(metrics["line_records"]),
            money(metrics["average_order_value"]),
        ],
    ]
    table = Table(metric_rows, colWidths=[130] * 4)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2f3ee")), ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 8)]))
    story += [table, Spacer(1, 0.15 * inch)]
    comparison = data["comparison"]
    if spec.report_type == "all":
        comparison_text = "Prior-period comparison is not applicable to an all-years report."
    elif comparison["total_spending"] is None:
        comparison_text = "Comparison unavailable: no records in the prior period."
    elif comparison["change_percent"] is None:
        comparison_text = f"Prior period spending: {money(comparison['total_spending'])}; percentage change unavailable because prior spending is zero."
    else:
        comparison_text = f"Prior period spending: {money(comparison['total_spending'])}; change: {comparison['change_percent']:+.2f}%."
    story.append(Paragraph(escape(comparison_text), styles["BodyText"]))
    section_info = [
        ("top_suppliers", "Top suppliers", "supplier", "supplier_analysis"),
        ("department_spending", "Department spending", "department", "department_analysis"),
        ("department_quarterly", "Leading departments by quarter", "department_period", "department_analysis"),
        ("monthly_trends", "Monthly trends", "month", "spending_trends"),
        ("quarterly_trends", "Quarterly trends", "quarter", "spending_trends"),
        ("category_spending", "Category spending", "category", "key_observations"),
        ("category_comparison", "Category comparison", "category", "key_observations"),
        ("custom_analysis", "Custom analysis", None, "key_observations"),
    ]
    story.extend([
        Paragraph("Spending overview", styles["Heading1"]),
        Paragraph(escape(narrative.spending_overview), styles["BodyText"]),
    ])
    for key, title, label, narrative_key in section_info:
        if key not in spec.sections:
            continue
        rows = data.get(key, [])
        story.extend([
            Spacer(1, 0.15 * inch),
            Paragraph(title, styles["Heading1"]),
            Paragraph(escape(getattr(narrative, narrative_key)), styles["BodyText"]),
        ])
        if not rows:
            story.append(Paragraph("No matching records.", styles["BodyText"]))
            continue
        if label and key != "custom_analysis":
            chart_name = {"top_suppliers": "supplier", "department_spending": "department", "department_quarterly": "department", "monthly_trends": "monthly", "quarterly_trends": "quarterly", "category_spending": "category", "category_comparison": "category"}[key]
            if chart_name in spec.charts:
                if key == "department_quarterly":
                    period_totals = {}
                    for row in rows:
                        period = f"{row['year']} Q{row['quarter']}"
                        period_totals[period] = (
                            period_totals.get(period, 0) + row["total_spending"]
                        )
                    chart_rows = [
                        {"period": period, "total_spending": value}
                        for period, value in period_totals.items()
                    ]
                    story.append(chart(
                        chart_rows, "period", "Selected departments by quarter"
                    ))
                else:
                    story.append(chart(rows, label, title))
        if key == "custom_analysis":
            columns = list(dict.fromkeys(column for row in rows for column in row))[:5]
        elif key == "category_comparison":
            columns = ["category", "total_spending", "prior_spending", "change_percent"]
        elif key == "department_quarterly":
            columns = ["year", "quarter", "department", "total_spending", "order_count"]
        elif chart_name in spec.tables:
            columns = [label, "total_spending", "order_count"]
            if key in {"top_suppliers", "department_spending", "category_spending"}:
                columns.append("share_percent")
        else:
            columns = []
        if columns:
            table_rows = [[column.replace("_", " ").title() for column in columns]]
            for row in rows[:200]:
                cells = []
                for column in columns:
                    value = row.get(column, "")
                    if column in {"total_spending", "prior_spending"} and isinstance(value, (int, float)):
                        value = money(value)
                    elif column in {"share_percent", "change_percent"} and isinstance(value, (int, float)):
                        value = f"{value:.2f}%"
                    cells.append(Paragraph(escape("Unavailable" if value is None else str(value)[:80]), styles["BodyText"]))
                table_rows.append(cells)
            section_table = Table(table_rows, colWidths=[520 / len(columns)] * len(columns), repeatRows=1, hAlign="LEFT")
            section_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2f3ee")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]), ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("PADDING", (0, 0), (-1, -1), 5)]))
            story.append(section_table)
    story.extend([
        Paragraph("Key observations", styles["Heading1"]),
        Paragraph(escape(narrative.key_observations), styles["BodyText"]),
        Paragraph("Conclusion", styles["Heading1"]),
        Paragraph(escape(narrative.conclusion), styles["BodyText"]),
        Paragraph("Methodology and source", styles["Heading1"]),
        Paragraph(
            "Spending sums line record total_price. Orders are distinct order_key values; "
            "average order value is the mean of each order's summed line values. Rankings "
            "use the same report filters. Periods use the year and quarter fields derived "
            "from creation_date. Missing prior-period data is not treated as zero growth.",
            styles["BodyText"],
        ),
        Paragraph(escape(SOURCE), styles["BodyText"]),
    ])
    SimpleDocTemplate(str(destination), pagesize=(612, 792), rightMargin=46, leftMargin=46, topMargin=50, bottomMargin=50).build(story)


def render_report_artifact(spec: ReportSpec, data: dict, narrative: ReportNarrative, report_id: str) -> None:
    """Render to a temporary file; this stage never marks a report complete."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    temporary = REPORT_DIR / f"{report_id}.tmp"
    preview = {
        "title": report_title(spec),
        "period": period_label(spec),
        "spec": spec.model_dump(mode="json"),
        "data": data,
        "narrative": narrative.model_dump(),
    }
    try:
        render_pdf(preview, temporary)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def save_rendered_report(spec: ReportSpec, data: dict, narrative: ReportNarrative, conversation_id: str | None, request_id: str, report_id: str) -> dict:
    document = {
        "_id": report_id,
        "title": report_title(spec),
        "period": period_label(spec),
        "status": "complete",
        "spec": spec.model_dump(mode="json"),
        "data": data,
        "narrative": narrative.model_dump(),
        "conversation_id": conversation_id,
        "request_id": request_id,
        "created_at": datetime.now(timezone.utc),
    }
    temporary = REPORT_DIR / f"{report_id}.tmp"
    destination = REPORT_DIR / f"{report_id}.pdf"
    if not temporary.is_file():
        raise FileNotFoundError("Rendered report artifact is missing.")
    try:
        temporary.replace(destination)
        reports_collection.insert_one(document)
    except Exception:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise
    return public_report(document)


def report_summary(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "period": document["period"],
        "status": document["status"],
        "conversation_id": document.get("conversation_id"),
        "created_at": document["created_at"].isoformat(),
    }


def public_report(document: dict) -> dict:
    return {
        **report_summary(document),
        "spec": document["spec"],
        "data": document["data"],
        "narrative": document["narrative"],
    }


def get_report(report_id: str) -> dict | None:
    document = reports_collection.find_one({"_id": report_id, "status": "complete"})
    return public_report(document) if document else None


def list_reports() -> list[dict]:
    documents = reports_collection.find(
        {"status": "complete"},
        {"title": 1, "period": 1, "status": 1, "conversation_id": 1, "created_at": 1},
    ).sort("created_at", -1).limit(100)
    return [report_summary(document) for document in documents]


def csv_export(report: dict, section: str) -> str:
    if section in {"spending_overview", "order_statistics"}:
        rows = [report["data"]["overview"]]
    else:
        rows = report["data"].get(section)
    if not isinstance(rows, list):
        raise ValueError("This report has no such tabular section.")
    output = io.StringIO()
    empty_columns = {
        "top_suppliers": ["supplier", "total_spending", "order_count", "line_records", "share_percent"],
        "department_spending": ["department", "total_spending", "order_count", "line_records", "share_percent"],
        "department_quarterly": ["year", "quarter", "department", "total_spending", "order_count"],
        "category_spending": ["category", "total_spending", "order_count", "line_records", "share_percent"],
        "monthly_trends": ["month", "total_spending", "order_count"],
        "quarterly_trends": ["quarter", "total_spending", "order_count"],
        "category_comparison": ["category", "total_spending", "prior_spending", "change_percent"],
    }
    columns = list(dict.fromkeys(key for row in rows for key in row)) if rows else empty_columns.get(section, [])
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            key: ("'" + value if isinstance(value, str) and value.startswith(
                ("=", "+", "-", "@", "\t", "\r")
            ) else value)
            for key, value in row.items()
        })
    return output.getvalue()
