import unittest

from app.evaluation.criteria import (
    analytical_correctness,
    conversation_context,
    mongodb_query_validity,
    presentation_correctness,
    route_accuracy,
)
from app.evaluation.dataset import EVALUATION_CASES


class EvaluationCriteriaTests(unittest.TestCase):
    def example(self, **overrides):
        outputs = {
            "expected_routes": ["analytical", "contextual_content"],
            "expected_query_executions": 1,
            "required_pipeline_fields": [["supplier_name", "total_price"], []],
            "expected_visualization": "bar",
            "expected_answer_terms": ["supplier"],
        }
        outputs.update(overrides)
        return {"outputs": outputs}

    def evaluation_run(self, turns):
        return {"outputs": {"turns": turns}}

    def passing_turns(self):
        return [
            {
                "route_category": "analytical",
                "pipeline": [
                    {"$group": {"_id": "$supplier_name", "spend": {"$sum": "$total_price"}}},
                    {"$limit": 5},
                ],
                "is_valid": True,
                "execution_error": None,
                "answer": "The top suppliers are listed below.",
                "visualization": None,
            },
            {
                "route_category": "contextual_content",
                "pipeline": [],
                "is_valid": False,
                "execution_error": None,
                "answer": "Here is the supplier chart.",
                "visualization": {"type": "bar", "data": []},
            },
        ]

    def test_dataset_covers_all_requested_behavior_categories(self):
        categories = {case.category for case in EVALUATION_CASES}
        self.assertTrue({
            "greeting", "analytical", "follow_up", "chart_request",
            "table_request", "invalid", "ambiguous",
        }.issubset(categories))

    def test_all_criteria_pass_for_a_conforming_follow_up(self):
        run = self.evaluation_run(self.passing_turns())
        example = self.example()

        for evaluator in (
            route_accuracy,
            mongodb_query_validity,
            analytical_correctness,
            presentation_correctness,
            conversation_context,
        ):
            with self.subTest(evaluator=evaluator.__name__):
                self.assertTrue(evaluator(run, example)["score"])

    def test_criteria_detect_route_pipeline_and_presentation_regressions(self):
        turns = self.passing_turns()
        turns[0]["route_category"] = "contextual_content"
        turns[0]["pipeline"] = []
        turns[1]["answer"] = "```mermaid\nchart\n```"

        run = self.evaluation_run(turns)
        example = self.example()

        self.assertFalse(route_accuracy(run, example)["score"])
        self.assertFalse(mongodb_query_validity(run, example)["score"])
        self.assertFalse(presentation_correctness(run, example)["score"])


if __name__ == "__main__":
    unittest.main()
