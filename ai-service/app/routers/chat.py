import asyncio
import json
from contextlib import suppress

from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ConversationMessages,
    ConversationSummary,
)

from app.services.chat_service import (
    process_chat_message,
    stream_chat_message,
)
from app.services.conversation_service import (
    ConversationNotFoundError,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Assistant"],
)


@router.get("/conversations", response_model=list[ConversationSummary])
def conversation_list():
    return list_conversations()


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationMessages,
)
def conversation_detail(conversation_id: str):
    try:
        return {
            "conversation": get_conversation(conversation_id),
            "messages": list_messages(conversation_id),
        }
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def conversation_delete(conversation_id: str):
    try:
        delete_conversation(conversation_id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def events():
        stream = stream_chat_message(request.message, request.conversation_id)
        pending = None
        try:
            pending = asyncio.create_task(anext(stream))
            while True:
                ready, _ = await asyncio.wait({pending}, timeout=15)
                if not ready:
                    yield ": keep-alive\n\n"
                    continue
                try:
                    event = pending.result()
                except StopAsyncIteration:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                pending = asyncio.create_task(anext(stream))
        finally:
            if pending is not None:
                pending.cancel()
                with suppress(asyncio.CancelledError, StopAsyncIteration):
                    await pending
            await stream.aclose()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
):

    try:

        return process_chat_message(
            message=request.message,
            conversation_id=(
                request.conversation_id
            ),
        )

    except Exception as error:

        print(
            f"AI assistant error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The AI assistant was unable "
                "to process the request."
            ),
        )
