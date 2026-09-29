from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.procurement import router as procurement_router
from app.routers.orders import router as orders_router
from app.routers.suppliers import router as suppliers_router
from app.routers.departments import router as departments_router


app = FastAPI(
    title="Procurement Analytics API"
)


@app.get("/")
def root():
    return {
        "message": "Procurement API is running"
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
app.include_router(orders_router)
app.include_router(suppliers_router)
app.include_router(departments_router)
