"""MongoDB persistence for chat conversations and their messages."""

from datetime import datetime, timezone
from typing import Any

from app.database.mongodb import conversations_collection, messages_collection


MAX_CONTEXT_MESSAGES = 40


class ConversationNotFoundError(Exception):
    pass


def _as_utc(value: datetime) -> datetime:
    # PyMongo returns naive UTC datetimes unless the client opts into tz-aware
    # decoding. Make the API timezone-explicit without changing other queries.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _conversation(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "created_at": _as_utc(document["created_at"]),
        "updated_at": _as_utc(document["updated_at"]),
    }


def _message(document: dict[str, Any]) -> dict[str, Any]:
    metadata = document.get("metadata", {})
    return {
        "id": str(document["_id"]),
        "conversation_id": document["conversation_id"],
        "turn_id": document["turn_id"],
        "role": document["role"],
        "content": document["content"],
        "created_at": _as_utc(document["created_at"]),
        "query_description": metadata.get("query_description"),
        "pipeline": metadata.get("pipeline"),
        "result_count": metadata.get("result_count", 0),
        "retry_count": metadata.get("retry_count", 0),
    }


def _title_from(message: str) -> str:
    compact = " ".join(message.split())
    return compact if len(compact) <= 60 else f"{compact[:57].rstrip()}..."


def get_conversation(conversation_id: str) -> dict[str, Any]:
    document = conversations_collection.find_one({"_id": conversation_id})
    if document is None:
        raise ConversationNotFoundError(conversation_id)
    return _conversation(document)


def list_conversations() -> list[dict[str, Any]]:
    documents = conversations_collection.find().sort("updated_at", -1)
    return [_conversation(document) for document in documents]


def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    documents = messages_collection.find(
        {"conversation_id": conversation_id}
    ).sort([("created_at", 1), ("_id", 1)])
    return [_message(document) for document in documents]


def load_chat_history(conversation_id: str | None) -> list[dict[str, str]]:
    if conversation_id is None:
        return []

    get_conversation(conversation_id)
    # Context is deliberately bounded, while the history endpoint returns every
    # stored message for display in the UI.
    documents = list(
        messages_collection.find(
            {"conversation_id": conversation_id},
            {"role": 1, "content": 1},
        )
        .sort([("created_at", -1), ("_id", -1)])
        .limit(MAX_CONTEXT_MESSAGES)
    )
    documents.reverse()
    return [
        {"role": document["role"], "content": document["content"]}
        for document in documents
    ]


def save_turn(
    *,
    conversation_id: str,
    turn_id: str,
    question: str,
    response: dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc)
    conversations_collection.update_one(
        {"_id": conversation_id},
        {
            "$setOnInsert": {
                "title": _title_from(question),
                "created_at": now,
            },
            "$set": {"updated_at": now},
        },
        upsert=True,
    )

    messages_collection.update_one(
        {"conversation_id": conversation_id, "turn_id": turn_id, "role": "user"},
        {
            "$setOnInsert": {
                "conversation_id": conversation_id,
                "turn_id": turn_id,
                "role": "user",
                "content": question,
                "created_at": now,
            }
        },
        upsert=True,
    )
    messages_collection.update_one(
        {"conversation_id": conversation_id, "turn_id": turn_id, "role": "assistant"},
        {
            "$setOnInsert": {
                "conversation_id": conversation_id,
                "turn_id": turn_id,
                "role": "assistant",
                "content": response["answer"],
                "created_at": now,
                "metadata": {
                    "query_description": response.get("query_description"),
                    "pipeline": response.get("pipeline"),
                    "result_count": response.get("result_count", 0),
                    "retry_count": response.get("retry_count", 0),
                },
            }
        },
        upsert=True,
    )
