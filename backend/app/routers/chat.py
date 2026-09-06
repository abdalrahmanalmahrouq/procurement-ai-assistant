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
)


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Assistant"],
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