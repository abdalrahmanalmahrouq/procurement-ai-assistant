"""Offline report workflow, data, export, and streaming regression tests."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pydantic import ValidationError

with patch("pymongo.MongoClient"):
    from app.ai.agent.graph import procurement_graph, route_after_classification
    from app.ai.agent.report_graph import gather_report_data, plan_report
    from app.models.report import ReportNarrative, ReportSpec
    from app.services.chat_service import initial_state, stream_chat_message
    from app.routers.reports import report_or_404
    from app.services.report_service import (
        csv_export, gather_standard_data, render_pdf, report_match,
        render_report_artifact, save_rendered_report, report_title, validate_report,
    )


def narrative():
    return ReportNarrative(
        executive_summary="Procurement activity is summarized below.",
        spending_overview="Spending reflects the filtered records.",
        supplier_analysis="Suppliers are ranked by spending.",
        department_analysis="Departments are ranked by spending.",
        spending_trends="Activity varied across the period.",
        key_observations="The tables show the measured distribution.",
        conclusion="The report reflects available source records.",
    )


def report_data():
    return {
        "overview": {"total_spending": 150.0, "order_count": 2, "line_records": 3, "average_order_value": 75.0},
        "comparison": {"period": "2013", "total_spending": None, "change_percent": None},
        "top_suppliers": [{"supplier": "Acme", "total_spending": 100.0, "order_count": 1, "line_records": 2, "share_percent": 66.67}],
        "department_spending": [{"department": "Health", "total_spending": 150.0, "order_count": 2, "line_records": 3, "share_percent": 100.0}],
        "monthly_trends": [{"month": 1, "total_spending": 150.0, "order_count": 2}],
        "quarterly_trends": [{"quarter": 1, "total_spending": 150.0, "order_count": 2}],
        "category_spending": [{"category": "Medical", "total_spending": 150.0, "order_count": 2, "line_records": 3, "share_percent": 100.0}],
    }


class ReportTests(unittest.TestCase):
    def test_annual_quarterly_and_invalid_periods(self):
        self.assertEqual(report_match(ReportSpec(year=2014)), {"year": 2014})
        self.assertEqual(report_title(ReportSpec(year=2014, report_focus="supplier")), "2014 Supplier Procurement Report")
        supplier_match = report_match(ReportSpec(year=2014, supplier="ACME"))
        self.assertEqual(supplier_match["$or"], [{"supplier_code": "ACME"}, {"supplier_name": "ACME"}])
        self.assertEqual(report_match(ReportSpec(report_type="quarterly", year=2014, quarter=2, department="Health")), {"year": 2014, "quarter": 2, "department_name": "Health"})
        with self.assertRaises(ValidationError):
            ReportSpec(report_type="quarterly", year=2014)
        with self.assertRaises(ValidationError):
            ReportSpec(year=2014, quarter=2)

    def test_natural_language_planning_and_builder_bypass(self):
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = ReportSpec(year=2014, ranking_limit=5)
        with patch("app.ai.agent.report_graph.get_llm", return_value=model):
            planned = plan_report({"question": "Generate a 2014 report with top 5 suppliers"})
        self.assertEqual(planned["report_spec"]["ranking_limit"], 5)
        with patch("app.ai.agent.report_graph.get_llm") as llm:
            builder = plan_report({"question": "Generate report", "report_spec_input": ReportSpec(report_type="quarterly", year=2014, quarter=3).model_dump()})
            llm.assert_not_called()
        self.assertEqual(builder["report_spec"]["quarter"], 3)
        self.assertEqual(route_after_classification({"route_category": "analytical", "question": "Generate a report"}), "report")
        self.assertEqual(route_after_classification({"route_category": "analytical", "question": "Top suppliers?"}), "analytical")

    def test_unspecified_period_and_it_goods_request_never_invents_a_year(self):
        question = (
            "Generate a report comparing IT Goods spending across the five "
            "highest-spending departments, broken down by quarter."
        )
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = ReportSpec(
            report_focus="department",
            year=2025,
            category="IT Goods",
            sections=["department_spending", "quarterly_trends"],
        )
        with patch("app.ai.agent.report_graph.get_llm", return_value=model):
            planned = ReportSpec.model_validate(plan_report({"question": question})["report_spec"])
        self.assertEqual(planned.report_type, "all")
        self.assertIsNone(planned.year)
        self.assertIsNone(planned.category)
        self.assertEqual(planned.acquisition_type, "IT Goods")
        self.assertEqual(planned.ranking_limit, 5)
        self.assertIn("department_quarterly", planned.sections)
        self.assertEqual(report_match(planned), {"acquisition_type": "IT Goods"})
        self.assertEqual(report_title(planned), "All available years Department Procurement Report")

    def test_department_quarterly_uses_one_scope_and_distinct_year_quarters(self):
        from app.services.report_service import department_quarterly
        pipelines = []
        def aggregate(pipeline, **kwargs):
            pipelines.append(pipeline)
            if any("$limit" in stage for stage in pipeline):
                return [{"department": "Health", "total_spending": 100, "order_count": 1, "line_records": 1}]
            return [{"department": "Health", "year": 2014, "quarter": 2, "total_spending": 100, "order_count": 1}]
        with patch("app.services.report_service.procurement_collection.aggregate", side_effect=aggregate):
            rows = department_quarterly({"acquisition_type": "IT Goods"}, 5)
        self.assertEqual(rows[0]["department_period"], "Health · 2014 Q2")
        self.assertTrue(all(pipeline[0]["$match"]["acquisition_type"] == "IT Goods" for pipeline in pipelines))
        self.assertTrue(all("year" not in pipeline[0]["$match"] for pipeline in pipelines))
        self.assertEqual(pipelines[-1][1]["$group"]["_id"]["year"], "$year")
        self.assertEqual(pipelines[-1][1]["$group"]["_id"]["quarter"], "$quarter")

    def test_all_years_aggregation_keeps_years_separate_and_skips_comparison(self):
        pipelines = []
        def aggregate(pipeline, **kwargs):
            pipelines.append(pipeline)
            if pipeline[-1].get("$project", {}).get("average_order_value") is not None:
                return [{"total_spending": 50, "order_count": 1, "line_records": 1, "average_order_value": 50}]
            if any("$_id.period" in str(stage) for stage in pipeline):
                return [{"year": 2014, "quarter": 2, "total_spending": 50, "order_count": 1}]
            return []
        spec = ReportSpec(report_type="all", acquisition_type="IT Goods", sections=["spending_overview", "quarterly_trends"])
        with patch("app.services.report_service.procurement_collection.aggregate", side_effect=aggregate):
            data = gather_standard_data(spec)
        self.assertEqual(data["comparison"]["period"], "Not applicable")
        self.assertIsNone(data["comparison"]["total_spending"])
        self.assertEqual(data["quarterly_trends"][0]["quarter"], "2014 Q2")
        self.assertTrue(all(pipeline[0]["$match"] == {"acquisition_type": "IT Goods"} for pipeline in pipelines))
        self.assertEqual(len(pipelines), 2)

    def test_malformed_planning_output_and_empty_data(self):
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = {"year": "invalid"}
        with patch("app.ai.agent.report_graph.get_llm", return_value=model):
            with self.assertRaises(ValidationError):
                plan_report({"question": "Generate report"})
        with patch("app.services.report_service.procurement_collection.aggregate", return_value=[]):
            data = gather_standard_data(ReportSpec(year=2014))
        self.assertEqual(data["overview"]["order_count"], 0)
        self.assertEqual(data["top_suppliers"], [])
        self.assertIsNone(data["comparison"]["change_percent"])

    def test_filtered_aggregations_and_unavailable_comparison(self):
        pipelines = []
        def aggregate(pipeline, **kwargs):
            pipelines.append(pipeline)
            match = pipeline[0]["$match"]
            if "supplier_name" in match and isinstance(match["supplier_name"], dict):
                return [{"supplier": "Acme", "total_spending": 100, "order_count": 1, "line_records": 2}]
            if pipeline[-1].get("$project") == {"_id": 0}:
                return [{"total_spending": 150, "order_count": 2, "line_records": 3, "average_order_value": 75}] if match["year"] == 2014 else []
            return []
        spec = ReportSpec(year=2014, department="Health", sections=["spending_overview", "top_suppliers"])
        with patch("app.services.report_service.procurement_collection.aggregate", side_effect=aggregate):
            data = gather_standard_data(spec)
        self.assertEqual(data["overview"]["average_order_value"], 75)
        self.assertEqual(data["top_suppliers"][0]["share_percent"], 66.67)
        self.assertIsNone(data["comparison"]["change_percent"])
        self.assertTrue(all(pipeline[0]["$match"]["department_name"] == "Health" for pipeline in pipelines))

    def test_category_comparison_uses_prior_period_and_handles_missing_rows(self):
        def aggregate(pipeline, **kwargs):
            match = pipeline[0]["$match"]
            if pipeline[-1].get("$project") == {"_id": 0}:
                return [{"total_spending": 150, "order_count": 2, "line_records": 2, "average_order_value": 75}] if match["year"] == 2014 else []
            if "commodity_title" in match:
                return [{"category": "Medical", "total_spending": 150, "order_count": 2, "line_records": 2}] if match["year"] == 2014 else [{"category": "Medical", "total_spending": 100, "order_count": 1, "line_records": 1}]
            return []
        with patch("app.services.report_service.procurement_collection.aggregate", side_effect=aggregate):
            data = gather_standard_data(ReportSpec(year=2014, sections=["category_comparison"]))
        self.assertEqual(data["category_comparison"][0]["change_percent"], 50)
        self.assertEqual(data["category_comparison"][0]["prior_spending"], 100)

    def test_ranking_keeps_filter_on_the_ranked_field(self):
        from app.services.report_service import ranking
        with patch("app.services.report_service.procurement_collection.aggregate", return_value=[]) as aggregate:
            ranking({"year": 2014, "supplier_name": "Acme"}, "supplier_name", "supplier", 5)
        self.assertEqual(aggregate.call_args.args[0][0]["$match"]["supplier_name"], "Acme")

    def test_custom_analysis_reuses_validated_query_and_scope(self):
        spec = ReportSpec(year=2014, sections=["custom_analysis"], custom_requirements=["Count items"])
        generated = {"pipeline": [{"$count": "items"}]}
        with patch("app.ai.agent.report_graph.gather_standard_data", return_value=report_data()), patch("app.ai.agent.report_graph.generate_query", return_value=generated), patch("app.ai.agent.report_graph.execute_query", return_value={"query_result": [{"items": 3}], "execution_error": None}) as execute:
            data = gather_report_data({"report_spec": spec.model_dump()})["report_data"]
        self.assertEqual(data["custom_analysis"], [{"items": 3, "requirement": "Count items"}])
        self.assertEqual(execute.call_args.args[0]["pipeline"][0], {"$match": {"year": 2014}})

    def test_validation_rejects_unverified_numbers_and_missing_sections(self):
        spec = ReportSpec(year=2014)
        validate_report(spec, report_data(), narrative())
        bad = narrative().model_copy(update={"conclusion": "Spending grew 30 percent."})
        with self.assertRaises(ValueError):
            validate_report(spec, report_data(), bad)
        with self.assertRaises(ValueError):
            validate_report(spec, {"overview": report_data()["overview"]}, narrative())
        malformed = report_data()
        malformed["top_suppliers"] = [{"supplier": "Acme"}]
        with self.assertRaises(ValueError):
            validate_report(spec, malformed, narrative())

    def test_pdf_csv_and_persistence(self):
        spec = ReportSpec(year=2014)
        data = report_data()
        with tempfile.TemporaryDirectory() as directory, patch("app.services.report_service.REPORT_DIR", Path(directory)), patch("app.services.report_service.reports_collection.insert_one") as insert:
            report_id = str(uuid4())
            render_report_artifact(spec, data, narrative(), report_id)
            report = save_rendered_report(spec, data, narrative(), "conversation", "request", report_id)
            content = (Path(directory) / f"{report['id']}.pdf").read_bytes()
            self.assertTrue(content.startswith(b"%PDF"))
            self.assertEqual(insert.call_args.args[0]["request_id"], "request")
        csv_text = csv_export(report, "top_suppliers")
        self.assertIn("Acme,100.0,1,2,66.67", csv_text)

    def test_zero_prior_spending_renders_without_a_growth_rate(self):
        spec = ReportSpec(year=2014)
        data = report_data()
        data["comparison"] = {"period": "2013", "total_spending": 0, "change_percent": None}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "zero-prior.pdf"
            render_pdf({"title": "2014 Procurement Report", "period": "2014", "spec": spec.model_dump(), "data": data, "narrative": narrative().model_dump()}, target)
            self.assertTrue(target.read_bytes().startswith(b"%PDF"))

    def test_export_failure_never_creates_a_completed_record(self):
        with tempfile.TemporaryDirectory() as directory, patch("app.services.report_service.REPORT_DIR", Path(directory)), patch("app.services.report_service.render_pdf", side_effect=RuntimeError("PDF failed")), patch("app.services.report_service.reports_collection.insert_one") as insert:
            with self.assertRaises(RuntimeError):
                render_report_artifact(ReportSpec(year=2014), report_data(), narrative(), str(uuid4()))
            insert.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_database_save_failure_removes_pdf(self):
        with tempfile.TemporaryDirectory() as directory, patch("app.services.report_service.REPORT_DIR", Path(directory)), patch("app.services.report_service.reports_collection.insert_one", side_effect=RuntimeError("save failed")):
            report_id = str(uuid4())
            spec = ReportSpec(year=2014)
            render_report_artifact(spec, report_data(), narrative(), report_id)
            with self.assertRaises(RuntimeError):
                save_rendered_report(spec, report_data(), narrative(), None, "request", report_id)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_report_lookup_rejects_invalid_and_missing_ids(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            report_or_404("../../other-file")
        with patch("app.routers.reports.get_report", return_value=None):
            with self.assertRaises(HTTPException):
                report_or_404(str(uuid4()))

    def test_saved_report_api_and_csv_download(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routers.reports import router
        report = {"id": str(uuid4()), "title": "2014 Procurement Report", "period": "2014", "status": "complete", "created_at": "2026-09-29T00:00:00+00:00", "conversation_id": None, "spec": ReportSpec(year=2014).model_dump(mode="json"), "data": report_data(), "narrative": narrative().model_dump()}
        app = FastAPI()
        app.include_router(router)
        with patch("app.routers.reports.get_report", return_value=report):
            client = TestClient(app)
            self.assertEqual(client.get(f"/api/reports/{report['id']}").json()["title"], report["title"])
            csv_response = client.get(f"/api/reports/{report['id']}/csv/top_suppliers")
            self.assertEqual(csv_response.status_code, 200)
            self.assertIn("Acme,100.0,1,2,66.67", csv_response.text)
            with tempfile.TemporaryDirectory() as directory:
                pdf_path = Path(directory) / f"{report['id']}.pdf"
                pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
                with patch("app.routers.reports.REPORT_DIR", Path(directory)):
                    preview = client.get(f"/api/reports/{report['id']}/pdf")
                    download = client.get(f"/api/reports/{report['id']}/pdf?download=1")
                self.assertEqual(preview.status_code, 200)
                self.assertTrue(preview.headers["content-disposition"].startswith("inline;"))
                self.assertTrue(download.headers["content-disposition"].startswith("attachment;"))

    def test_builder_report_graph_and_sse_progress(self):
        spec = ReportSpec(year=2014)
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = narrative()
        result = {"id": str(uuid4()), "title": "2014 Procurement Report", "period": "2014", "status": "complete", "created_at": "2026-09-29T00:00:00+00:00", "conversation_id": "conversation"}
        with patch("app.ai.agent.report_graph.get_llm", return_value=model), patch("app.ai.agent.report_graph.gather_standard_data", return_value=report_data()), patch("app.ai.agent.report_graph.render_report_artifact"), patch("app.ai.agent.report_graph.save_rendered_report", return_value=result):
            output = procurement_graph.invoke(initial_state("Generate report", report_spec=spec.model_dump(), request_id="request", conversation_id="conversation"), config={"configurable": {"thread_id": str(uuid4())}})
        self.assertEqual(output["report"]["id"], result["id"])
        self.assertIn("ready", output["answer"])


class ReportStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_narrative_emits_error_without_saving(self):
        spec = ReportSpec(year=2014)
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = narrative().model_copy(update={"conclusion": "Spending was 10 dollars."})
        with patch("app.ai.agent.report_graph.get_llm", return_value=model), patch("app.ai.agent.report_graph.gather_standard_data", return_value=report_data()), patch("app.ai.agent.report_graph.render_report_artifact") as render, patch("app.ai.agent.report_graph.save_rendered_report") as save, patch("app.services.chat_service.start_turn"), patch("app.services.chat_service.finish_turn"), patch("app.services.chat_service.load_chat_history", return_value=[]), patch("app.services.chat_service.load_query_context", return_value=None):
            events = [event async for event in stream_chat_message("Generate report", report_spec=spec.model_dump(), conversation_id="conversation")]
        self.assertEqual(events[-1]["type"], "error")
        self.assertEqual(events[-1]["error"]["stage"], "validate_report_content")
        render.assert_not_called()
        save.assert_not_called()

    async def test_progress_and_success(self):
        spec = ReportSpec(year=2014)
        model = MagicMock()
        model.with_structured_output.return_value.invoke.return_value = narrative()
        result = {"id": str(uuid4()), "title": "2014 Procurement Report", "period": "2014", "status": "complete", "created_at": "2026-09-29T00:00:00+00:00", "conversation_id": "conversation"}
        with patch("app.ai.agent.report_graph.get_llm", return_value=model), patch("app.ai.agent.report_graph.gather_standard_data", return_value=report_data()), patch("app.ai.agent.report_graph.render_report_artifact"), patch("app.ai.agent.report_graph.save_rendered_report", return_value=result), patch("app.services.chat_service.start_turn"), patch("app.services.chat_service.finish_turn"), patch("app.services.chat_service.load_chat_history", return_value=[]), patch("app.services.chat_service.load_query_context", return_value=None):
            events = [event async for event in stream_chat_message("Generate report", report_spec=spec.model_dump(), conversation_id="conversation")]
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["report"]["id"], result["id"])
        self.assertTrue(any(event.get("step") == "gather_report_data" for event in events))

