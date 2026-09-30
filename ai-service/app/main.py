import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.errors import ApplicationError
from app.observability import REQUEST_ID_HEADER, get_request_id
from app.routers.chat import router as chat_router
from app.routers.reports import router as reports_router


app = FastAPI(title="Procurement AI Service")
logger = logging.getLogger(__name__)


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, error: ApplicationError):
    request_id = get_request_id(request)
    return JSONResponse(
        status_code=error.status_code,
        content=error.payload(request_id),
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError):
    request_id = get_request_id(request)
    app_error = ApplicationError(
        "REQUEST_INVALID",
        "request",
        "Please provide a valid chat request.",
        False,
        422,
    )
    return JSONResponse(
        status_code=app_error.status_code,
        content=app_error.payload(request_id),
        headers={REQUEST_ID_HEADER: request_id},
    )



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
    return {"message": "Procurement AI service is running"}


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
app.include_router(reports_router)
