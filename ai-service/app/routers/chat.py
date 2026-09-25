import asyncio
import json
import logging
from contextlib import suppress

from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ConversationMessages,
    ConversationSummary,
)
from app.errors import ApplicationError, classify_error
from app.observability import REQUEST_ID_HEADER, get_request_id

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
logger = logging.getLogger(__name__)


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
async def chat_stream(request: ChatRequest, http_request: Request):
    request_id = get_request_id(http_request)

    async def events():
        stream = stream_chat_message(
            request.message,
            request.conversation_id,
            request_id=request_id,
        )
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
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            REQUEST_ID_HEADER: request_id,
        },
    )


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    http_request: Request,
    response: Response,
):
    request_id = get_request_id(http_request)
    response.headers[REQUEST_ID_HEADER] = request_id

    try:

        return process_chat_message(
            message=request.message,
            conversation_id=(
                request.conversation_id
            ),
            request_id=request_id,
        )

    except ApplicationError as app_error:
        return JSONResponse(
            status_code=app_error.status_code,
            content=app_error.payload(request_id),
            headers={REQUEST_ID_HEADER: request_id},
        )
    except Exception as error:
        logger.exception("AI assistant request failed request_id=%s", request_id)
        app_error = classify_error(error)
        return JSONResponse(
            status_code=app_error.status_code,
            content=app_error.payload(request_id),
            headers={REQUEST_ID_HEADER: request_id},
        )
