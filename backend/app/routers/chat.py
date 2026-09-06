import asyncio
import json
from contextlib import suppress

from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_service import (
    process_chat_message,
    stream_chat_message,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Assistant"],
)


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
