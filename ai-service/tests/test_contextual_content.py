import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from langchain_core.language_models.fake_chat_models import FakeListChatModel

with patch("pymongo.MongoClient"):
    from app.ai.agent.graph import procurement_graph
    from app.ai.models.visualization_model import Visualization, VisualizationDatum
    from app.services.chat_service import (
        chat_response,
        initial_state,
        reusable_query_context,
    )


class ContextualContentTests(unittest.TestCase):
    def test_metric_followup_reuses_result_without_another_query(self):
        route = MagicMock()
        route.with_structured_output.return_value.invoke.side_effect = [
            SimpleNamespace(route="analytical"),
            SimpleNamespace(route="contextual_content"),
        ]
        query = MagicMock()
        query.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
            pipeline_json='[{"$limit": 1}]',
            description="Highest-spending department.",
        )
        answer = FakeListChatModel(responses=["Public Works spent the most."])
        contextual = FakeListChatModel(
            responses=[
                "Here is the previous result as a metric card.\n\n"
                "```mermaid\nxychart-beta\nbar [123]\n```"
            ]
        )
        visualization = MagicMock()
        visualization.with_structured_output.return_value.invoke.return_value = (
            Visualization(
                type="metric",
                title="Top department",
                subtitle="",
                x_axis_label="",
                y_axis_label="",
                value_format="currency",
                data=[VisualizationDatum(label="Public Works", value=123)],
            )
        )
        collection = MagicMock()
        collection.aggregate.return_value = [
            {"department_name": "Public Works", "spend": 123}
        ]
        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        with (
            patch("app.ai.nodes.route_question.get_llm", return_value=route),
            patch("app.ai.nodes.generate_query.get_llm", return_value=query),
            patch("app.ai.nodes.generate_answer.get_llm", return_value=answer),
            patch(
                "app.ai.nodes.contextual_content.get_llm",
                return_value=contextual,
            ),
            patch(
                "app.ai.nodes.generate_visualization.get_llm",
                return_value=visualization,
            ),
            patch(
                "app.ai.nodes.execute_query.procurement_collection",
                collection,
            ),
        ):
            first = procurement_graph.invoke(
                initial_state("Which department spent the most?"),
                config=config,
            )
            second = procurement_graph.invoke(
                initial_state(
                    "Put that information in a metric card",
                    query_context=reusable_query_context(first),
                ),
                config=config,
            )

        response = chat_response(thread_id, second)
        self.assertEqual(second["route_category"], "contextual_content")
        self.assertNotIn("mermaid", response["answer"])
        self.assertEqual(response["visualization"]["type"], "metric")
        self.assertIsNone(response["pipeline"])
        self.assertEqual(
            query.with_structured_output.return_value.invoke.call_count,
            1,
        )
        self.assertEqual(collection.aggregate.call_count, 1)


if __name__ == "__main__":
    unittest.main()
