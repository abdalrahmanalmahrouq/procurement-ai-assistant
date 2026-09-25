import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.ai.nodes.generate_answer import generate_answer
from app.ai.nodes.handle_validation_failure import handle_validation_failure
from app.errors import ApplicationError, classify_error


class ErrorContractTests(unittest.TestCase):
    def test_model_timeout_is_safe_retryable_and_stage_specific(self):
        error = classify_error(TimeoutError("provider details"), "generate_query")

        self.assertEqual(error.code, "MODEL_TIMEOUT")
        self.assertEqual(error.stage, "generate_query")
        self.assertTrue(error.retryable)
        self.assertEqual(error.status_code, 504)
        self.assertNotIn("provider details", error.message)

    def test_exhausted_validation_repair_sets_controlled_graph_error(self):
        state = handle_validation_failure({"retry_count": 1})

        self.assertEqual(state["agent_error"]["code"], "QUERY_VALIDATION_FAILED")
        self.assertEqual(state["agent_error"]["stage"], "validate_query")
        self.assertTrue(state["agent_error"]["retryable"])

    def test_database_failure_is_not_an_empty_successful_answer(self):
        state = generate_answer({
            "question": "How much was spent?",
            "execution_error": "private database error",
        })

        self.assertEqual(state["agent_error"]["code"], "DATABASE_UNAVAILABLE")
        self.assertEqual(state["query_result"] if "query_result" in state else [], [])
        self.assertIn("temporarily unavailable", state["answer"])
        self.assertNotIn("private database error", state["answer"])

    def test_error_payload_preserves_request_id_without_internal_details(self):
        request_id = str(uuid4())
        error = ApplicationError("MODEL_UNAVAILABLE", "generate_query", "Try again.", True, 503)

        payload = error.payload(request_id, "conversation-1")

        self.assertEqual(payload["request_id"], request_id)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"]["code"], "MODEL_UNAVAILABLE")
        self.assertEqual(payload["conversation_id"], "conversation-1")


if __name__ == "__main__":
    unittest.main()
