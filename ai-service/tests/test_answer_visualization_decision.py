import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.ai.nodes.generate_answer import generate_answer
from app.ai.models.route_model import RouteDecision


class AnswerVisualizationDecisionTests(unittest.TestCase):
    def test_initial_router_schema_only_contains_the_route_decision(self):
        properties = RouteDecision.model_json_schema()["properties"]

        self.assertEqual(set(properties), {"route"})

    def answer(self, question: str):
        llm = MagicMock()
        llm.invoke.return_value = SimpleNamespace(content="Answer")
        state = {
            "question": question,
            "query_result": [{"supplier": "Acme", "spend": 100}],
            "query_description": "Ranks suppliers by spend.",
            "execution_error": None,
        }
        with patch("app.ai.nodes.generate_answer.get_llm", return_value=llm):
            return generate_answer(state)

    def test_named_visualization_is_detected_during_answer_generation(self):
        result = self.answer("Show the top suppliers in a bar chart")

        self.assertTrue(result["wants_visualization"])
        self.assertEqual(result["visualization_type"], "bar")

    def test_normal_analytical_answer_does_not_request_visualization(self):
        result = self.answer("Which supplier has the highest spending?")

        self.assertFalse(result["wants_visualization"])
        self.assertEqual(result["visualization_type"], "none")


if __name__ == "__main__":
    unittest.main()
