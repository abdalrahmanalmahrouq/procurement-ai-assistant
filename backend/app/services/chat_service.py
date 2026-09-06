from uuid import uuid4

from app.ai.agent.graph import (
    procurement_graph,
)


def process_chat_message(
    message: str,
    conversation_id: str | None = None,
):
    # --------------------------------
    # Create conversation if needed
    # --------------------------------

    if not conversation_id:
        conversation_id = str(
            uuid4()
        )

    # LangGraph configuration
    config = {
        "configurable": {
            "thread_id": conversation_id
        }
    }

    # --------------------------------
    # Run the complete AI agent
    # --------------------------------

    result = procurement_graph.invoke(
        {
            "question": message,
            "retry_count": 0,
        },
        config=config,
    )

    # --------------------------------
    # Shape backend response
    # --------------------------------

    return {
        "conversation_id":
            conversation_id,

        "answer":
            result.get(
                "answer",
                (
                    "I was unable to answer "
                    "that question."
                )
            ),

        "query_description":
            result.get(
                "query_description"
            ),

        "pipeline":
            result.get(
                "pipeline"
            ),

        "result_count":
            result.get(
                "result_count",
                0
            ),

        "retry_count":
            result.get(
                "retry_count",
                0
            ),
    }