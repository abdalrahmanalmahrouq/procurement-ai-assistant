from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.procurement import router as procurement_router


app = FastAPI(
    title="Penny Procurement AI API"
)


@app.get("/")
def root():
    return {
        "message": "Penny Procurement API is running"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(procurement_router)