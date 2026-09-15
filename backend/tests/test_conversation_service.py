import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Avoid opening a real Atlas connection while importing the service.
with patch("pymongo.MongoClient"):
    from app.services import conversation_service


class ConversationServiceTests(unittest.TestCase):
    def setUp(self):
        self.conversations = MagicMock()
        self.messages = MagicMock()
        self.collection_patches = [
            patch.object(
                conversation_service,
                "conversations_collection",
                self.conversations,
            ),
            patch.object(
                conversation_service,
                "messages_collection",
                self.messages,
            ),
        ]
        for collection_patch in self.collection_patches:
            collection_patch.start()
            self.addCleanup(collection_patch.stop)

    def test_save_turn_links_two_messages_and_keeps_the_first_title(self):
        conversation_service.save_turn(
            conversation_id="conversation-1",
            turn_id="turn-1",
            question="  Which   department spent the most?  ",
            response={
                "answer": "Public Works.",
                "pipeline": [{"$limit": 1}],
                "query_description": "Ranks departments.",
                "result_count": 1,
                "retry_count": 0,
            },
        )

        conversation_update = self.conversations.update_one.call_args.args[1]
        self.assertEqual(
            conversation_update["$setOnInsert"]["title"],
            "Which department spent the most?",
        )
        self.assertTrue(self.conversations.update_one.call_args.kwargs["upsert"])
        self.assertEqual(self.messages.update_one.call_count, 2)

        user_document = self.messages.update_one.call_args_list[0].args[1][
            "$setOnInsert"
        ]
        assistant_document = self.messages.update_one.call_args_list[1].args[1][
            "$setOnInsert"
        ]
        self.assertEqual(user_document["conversation_id"], "conversation-1")
        self.assertEqual(user_document["turn_id"], assistant_document["turn_id"])
        self.assertEqual(assistant_document["metadata"]["pipeline"], [{"$limit": 1}])

    def test_load_history_returns_recent_messages_in_chronological_order(self):
        self.conversations.find_one.return_value = {
            "_id": "conversation-1",
            "title": "A chat",
            "created_at": datetime(2026, 1, 1),
            "updated_at": datetime(2026, 1, 1),
        }
        cursor = MagicMock()
        self.messages.find.return_value = cursor
        cursor.sort.return_value.limit.return_value = [
            {"role": "assistant", "content": "Answer"},
            {"role": "user", "content": "Question"},
        ]

        history = conversation_service.load_chat_history("conversation-1")

        self.assertEqual(
            history,
            [
                {"role": "user", "content": "Question"},
                {"role": "assistant", "content": "Answer"},
            ],
        )
        cursor.sort.return_value.limit.assert_called_once_with(
            conversation_service.MAX_CONTEXT_MESSAGES
        )
        conversation = conversation_service.get_conversation("conversation-1")
        self.assertEqual(conversation["created_at"].tzinfo, timezone.utc)

    def test_missing_conversation_is_rejected(self):
        self.conversations.find_one.return_value = None
        with self.assertRaises(conversation_service.ConversationNotFoundError):
            conversation_service.load_chat_history("missing")


if __name__ == "__main__":
    unittest.main()
