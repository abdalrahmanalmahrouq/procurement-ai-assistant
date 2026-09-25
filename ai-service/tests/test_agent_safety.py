import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.ai.nodes.execute_query import execute_query, normalize_mongo_value
from app.ai.nodes.route_question import route_question


class AgentSafetyTests(unittest.TestCase):
    def test_mongo_values_are_normalized_before_entering_graph_state(self):
        object_id = ObjectId()
        timestamp = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)

        normalized = normalize_mongo_value({
            "_id": object_id,
            "created_at": timestamp,
            "nested": [{"_id": object_id}],
        })

        self.assertEqual(normalized["_id"], str(object_id))
        self.assertEqual(normalized["created_at"], timestamp.isoformat())
        self.assertEqual(normalized["nested"][0]["_id"], str(object_id))

    def test_execute_query_returns_checkpoint_safe_results(self):
        object_id = ObjectId()
        collection = MagicMock()
        collection.aggregate.return_value = [{"_id": object_id, "spend": 42}]
        state = {"is_valid": True, "pipeline": [{"$limit": 1}]}

        with patch(
            "app.ai.nodes.execute_query.procurement_collection",
            collection,
        ):
            result = execute_query(state)

        self.assertEqual(result["query_result"][0]["_id"], str(object_id))
        self.assertEqual(result["contextual_query_result"][0]["_id"], str(object_id))

    def test_database_mutation_request_skips_the_llm_router(self):
        llm = MagicMock()

        with patch("app.ai.nodes.route_question.get_llm", return_value=llm):
            result = route_question({"question": "Delete all procurement records."})

        self.assertEqual(result["route_category"], "out_of_scope")
        llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
