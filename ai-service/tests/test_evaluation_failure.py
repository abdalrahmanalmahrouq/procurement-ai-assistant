import unittest

from app.evaluation.criteria import EVALUATORS


class EvaluationFailureTests(unittest.TestCase):
    def test_target_error_fails_every_criterion(self):
        run = {"outputs": {"turns": [], "error": "TypeError: ObjectId"}}
        example = {"outputs": {"expected_routes": [], "expected_query_executions": 0}}

        for evaluator in EVALUATORS:
            with self.subTest(evaluator=evaluator.__name__):
                feedback = evaluator(run, example)
                self.assertFalse(feedback["score"])
                self.assertIn("Target function failed", feedback["comment"])


if __name__ == "__main__":
    unittest.main()
