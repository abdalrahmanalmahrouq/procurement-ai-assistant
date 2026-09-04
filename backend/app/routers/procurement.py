from fastapi import APIRouter

from app.services.procurement_service import (
    get_orders_by_quarter,
    get_average_order_value,
    get_highest_spending_quarter,
    get_top_departments,
    get_top_items,
    get_top_suppliers
)

router = APIRouter(
    prefix="/api/procurement",
    tags=["Procurement"]
)

@router.get("/orders/count")
def count_orders(year: int,quarter: int):
    total_orders = get_orders_by_quarter(
        year,
        quarter
    )

    return {
        "year": year,
        "quarter": quarter,
        "total_orders": total_orders
    }

@router.get("/spending/highest-quarter")
def highest_spending_qurater():
    return get_highest_spending_quarter()

@router.get("/suppliers/top")
def top_suppliers(limit: int = 10):
    return  get_top_suppliers(limit)

@router.get("/departments/top")
def top_departments(limit: int = 10):
    return get_top_departments(limit)

@router.get("/items/top")
def top_items(limit: int = 10):
    return get_top_items(limit)

@router.get("/orders/average-value")
def average_order_value():
    return {
        "average_order_value":
            get_average_order_value()
    }

@router.get("/dashboard/summary")
def dashboard_summary():
    return {
        "highest_spending_quarter":
            get_highest_spending_quarter(),

        "average_order_value":
            get_average_order_value(),

        "top_suppliers":
            get_top_suppliers(5),

        "top_departments":
            get_top_departments(5),

        "top_items":
            get_top_items(5)
    }