import logging
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import REQUEST_ID_HEADER, get_request_id
from app.routers.chat import router as chat_router


app = FastAPI(title="Penny Procurement AI Service")
logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = get_request_id(request)
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "AI service request failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        "AI service request completed request_id=%s method=%s path=%s "
        "status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started_at) * 1000,
    )
    return response


@app.get("/")
def root():
    return {"message": "Penny Procurement AI service is running"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER],
)

app.include_router(chat_router)
