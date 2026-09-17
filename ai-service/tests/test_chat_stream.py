"""Offline regression tests: real LangGraph, mocked model and database boundaries."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from pydantic import ValidationError
from pymongo.errors import OperationFailure

# MongoClient otherwise performs Atlas DNS resolution at import time.
with patch("pymongo.MongoClient"):
    from app.ai.agent.graph import procurement_graph
    from app.ai.models.visualization_model import Visualization, VisualizationDatum
    from app.models.chat import ChatRequest
    from app.routers.chat import router
    from app.services.chat_service import process_chat_message, stream_chat_message


class ChatStreamTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.route = MagicMock()
        self.route.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
            route="analytical",
        )
        self.query = MagicMock()
        self.query.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
            pipeline_json='[{"$count": "count"}]', description="Count procurement line records."
        )
        self.answer = FakeListChatModel(responses=["There are **3** line records."])
        self.visualization = MagicMock()
        self.visualization.with_structured_output.return_value.invoke.return_value = Visualization(
            type="bar",
            title="Records",
            subtitle="",
            x_axis_label="",
            y_axis_label="Records",
            value_format="number",
            data=[VisualizationDatum(label="All records", value=3)],
        )
        self.collection = MagicMock()
        self.collection.aggregate.return_value = [{"count": 3}]
        for target, value in [
            ("app.ai.nodes.route_question.get_llm", self.route),
            ("app.ai.nodes.generate_query.get_llm", self.query),
            ("app.ai.nodes.correct_query.get_llm", self.query),
            ("app.ai.nodes.generate_answer.get_llm", self.answer),
            ("app.ai.nodes.generate_visualization.get_llm", self.visualization),
        ]:
            patcher = patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch("app.ai.nodes.execute_query.procurement_collection", self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def collect(self, message="How many line records?", conversation_id=None):
        return [event async for event in stream_chat_message(message, conversation_id)]

    async def test_real_graph_streams_tokens_and_preserves_followup_history(self):
        events = await self.collect()
        self.assertEqual(events[0]["type"], "start")
        self.assertEqual(events[1]["step"], "route_question")
        deltas = [event["text"] for event in events if event["type"] == "answer_delta"]
        self.assertGreater(len(deltas), 1)
        self.assertEqual("".join(deltas), events[-1]["answer"])
        self.assertLess(next(i for i, e in enumerate(events) if e["type"] == "query"), next(i for i, e in enumerate(events) if e["type"] == "answer_delta"))
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["result_count"], 1)  # Aggregate rows, not source records.
        thread_id = events[0]["conversation_id"]
        stored_history = [
            {"role": "user", "content": "How many line records?"},
            {"role": "assistant", "content": events[-1]["answer"]},
        ]
        with patch(
            "app.services.chat_service.load_chat_history",
            return_value=stored_history,
        ):
            await self.collect("What about last year?", thread_id)
        messages = self.query.with_structured_output.return_value.invoke.call_args.args[0]
        self.assertEqual([message.type for message in messages], ["system", "human", "ai", "human"])
        self.assertEqual(messages[-1].content, "What about last year?")
        route_messages = self.route.with_structured_output.return_value.invoke.call_args.args[0]
        self.assertEqual([message.type for message in route_messages], ["system", "human", "ai", "human"])

    async def test_direct_routes_skip_query_generation_and_database(self):
        expected_phrases = {
            "greeting": "Hello!",
            "project_help": "I can answer questions",
            "out_of_scope": "I can only help",
        }

        for category, expected_phrase in expected_phrases.items():
            with self.subTest(category=category):
                self.route.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
                    route=category,
                )
                events = await self.collect(category)
                self.assertEqual(events[-1]["type"], "done")
                self.assertIn(expected_phrase, events[-1]["answer"])
                self.assertIsNone(events[-1]["pipeline"])
                self.assertFalse(any(event.get("type") == "query" for event in events))
                self.assertFalse(any(event.get("step") == "generate_query" for event in events))
                self.assertEqual(
                    "".join(event["text"] for event in events if event["type"] == "answer_delta"),
                    events[-1]["answer"],
                )

        self.query.with_structured_output.return_value.invoke.assert_not_called()
        self.collection.aggregate.assert_not_called()

    async def test_requested_visualization_is_generated_after_query_execution(self):
        self.route.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
            route="analytical",
        )

        events = await self.collect("Visualize the record count as a bar chart")

        visualization_event = next(
            event for event in events if event["type"] == "visualization"
        )
        self.assertEqual(visualization_event["visualization"]["type"], "bar")
        self.assertEqual(visualization_event["visualization"]["data"][0]["value"], 3.0)
        self.assertEqual(events[-1]["visualization"], visualization_event["visualization"])
        execute_index = next(
            index
            for index, event in enumerate(events)
            if event.get("step") == "execute_query" and event.get("status") == "complete"
        )
        visualization_index = events.index(visualization_event)
        self.assertLess(execute_index, visualization_index)

    async def test_validation_failure_after_success_does_not_reuse_results(self):
        first = await self.collect()
        self.query.with_structured_output.return_value.invoke.return_value = SimpleNamespace(
            pipeline_json='[{"$out": "forbidden"}]', description="Invalid query"
        )
        events = await self.collect("Another question", first[0]["conversation_id"])
        self.assertEqual(events[-1]["retry_count"], 1)
        self.assertEqual(events[-1]["result_count"], 0)
        self.assertIn("couldn't generate a valid", events[-1]["answer"])
        self.collection.aggregate.assert_called_once()
        self.assertEqual(len([e for e in events if e["type"] == "query"]), 2)

    async def test_execution_error_is_publicly_summarized_and_next_turn_recovers(self):
        self.collection.aggregate.side_effect = OperationFailure("secret database details")
        first = await self.collect()
        self.assertIn("unable to retrieve", first[-1]["answer"])
        self.assertNotIn("secret database details", json.dumps(first))
        self.assertTrue(any(e.get("step") == "execute_query" and e.get("status") == "error" for e in first))
        self.collection.aggregate.side_effect = None
        second = await self.collect("Try another query", first[0]["conversation_id"])
        self.assertEqual(second[-1]["answer"], "There are **3** line records.")

    async def test_empty_results_complete_without_answer_tokens(self):
        self.collection.aggregate.return_value = []
        events = await self.collect()
        self.assertEqual(events[-1]["result_count"], 0)
        self.assertIn("No matching", events[-1]["answer"])
        self.assertFalse(any(e["type"] == "answer_delta" for e in events))

    async def test_provider_failure_emits_sanitized_error(self):
        self.query.with_structured_output.return_value.invoke.side_effect = RuntimeError("secret provider details")
        with self.assertLogs("app.services.chat_service", level="ERROR"), patch(
            "app.services.chat_service.finish_turn"
        ) as finish_turn:
            events = await self.collect()
        self.assertEqual(events[-1]["type"], "error")
        self.assertNotIn("secret provider details", json.dumps(events))
        self.assertFalse(any(e["type"] == "done" for e in events))
        self.assertEqual(finish_turn.call_args.kwargs["status"], "error")

    async def test_raw_state_and_reasoning_are_not_forwarded(self):
        async def fake_stream(*args, **kwargs):
            yield "messages", (SimpleNamespace(content="private query tokens"), {"langgraph_node": "generate_query"})
            yield "messages", (SimpleNamespace(content=[{"type": "reasoning", "text": "private reasoning"}, {"type": "text", "text": "Public answer"}]), {"langgraph_node": "generate_answer"})
            yield "updates", {"save_conversation": {"answer": "Public answer", "query_result": [{"private": "raw records"}], "chat_history": [{"content": "private history"}]}}
        with patch.object(procurement_graph, "astream", side_effect=fake_stream):
            events = await self.collect()
        serialized = json.dumps(events)
        for private in ["private query tokens", "private reasoning", "raw records", "private history"]:
            self.assertNotIn(private, serialized)
        self.assertEqual([e["text"] for e in events if e["type"] == "answer_delta"], ["Public answer"])

    async def test_done_waits_for_graph_completion(self):
        checkpoint_finished = False

        async def fake_stream(*args, **kwargs):
            nonlocal checkpoint_finished
            yield "updates", {"save_conversation": {"answer": "Saved"}}
            checkpoint_finished = True

        with patch.object(procurement_graph, "astream", side_effect=fake_stream):
            async for event in stream_chat_message("A question"):
                if event["type"] == "done":
                    self.assertTrue(checkpoint_finished)

    async def test_disconnecting_closes_graph_iterator(self):
        closed = False

        async def fake_stream(*args, **kwargs):
            nonlocal closed
            try:
                yield "updates", {"generate_query": {"pipeline": [{"$count": "count"}]}}
            finally:
                closed = True

        with patch.object(procurement_graph, "astream", side_effect=fake_stream):
            stream = stream_chat_message("A question")
            await anext(stream)  # Conversation ID.
            await anext(stream)  # Initial progress.
            await anext(stream)  # First graph update.
            await stream.aclose()
        self.assertTrue(closed)

    def test_existing_json_endpoint_contract(self):
        result = process_chat_message("How many line records?", str(uuid4()))
        self.assertEqual(result["answer"], "There are **3** line records.")
        self.assertEqual(result["result_count"], 1)
        self.assertEqual(result["pipeline"], [{"$count": "count"}])
        self.assertIsNone(result["visualization"])

    def test_http_stream_and_input_validation(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client:
            response = client.post("/api/chat/stream", json={"message": "Count line records"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/event-stream", response.headers["content-type"])
            self.assertEqual(response.headers["x-accel-buffering"], "no")
            events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
            self.assertEqual(events[0]["type"], "start")
            self.assertEqual(events[-1]["type"], "done")
            self.assertEqual(client.post("/api/chat/stream", json={"message": "  "}).status_code, 422)
            self.assertEqual(client.post("/api/chat", json={"message": "Count line records"}).status_code, 200)
        with self.assertRaises(ValidationError):
            ChatRequest(message="a" * 4001)
        self.assertEqual(ChatRequest(message="  hello  ").message, "hello")


if __name__ == "__main__":
    unittest.main()
