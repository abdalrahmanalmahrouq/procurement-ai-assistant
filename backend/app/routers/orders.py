from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.services.order_service import (
    get_acquisition_type_breakdown,
    get_order_details,
    get_order_filter_options,
    get_order_value_distribution,
    get_orders,
    get_orders_summary,
    get_spend_over_time,
    search_suppliers,
)


router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("/summary")
def orders_summary():
    return get_orders_summary()


@router.get("/spend-over-time")
def spend_over_time(
    granularity: Literal["month", "quarter", "year"] = "quarter",
    year: int | None = None,
):
    return get_spend_over_time(granularity=granularity, year=year)


@router.get("/acquisition-types")
def acquisition_types(year: int | None = None):
    return get_acquisition_type_breakdown(year=year)


@router.get("/value-distribution")
def value_distribution():
    return get_order_value_distribution()


@router.get("/filter-options")
def filter_options():
    return get_order_filter_options()


@router.get("/suppliers/search")
def suppliers_search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
):
    return search_suppliers(query=q, limit=limit)


@router.get("")
def orders_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    year: int | None = None,
    quarter: int | None = Query(default=None, ge=1, le=4),
    fiscal_year: str | None = None,
    department: str | None = None,
    supplier: str | None = None,
    acquisition_type: str | None = None,
    acquisition_method: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    search: str | None = Query(default=None, max_length=100),
    sort_by: Literal[
        "creation_date",
        "total_value",
        "line_count",
        "purchase_order_number",
    ] = "creation_date",
    sort_direction: Literal["asc", "desc"] = "desc",
):
    return get_orders(
        page=page,
        page_size=page_size,
        year=year,
        quarter=quarter,
        fiscal_year=fiscal_year,
        department=department,
        supplier=supplier,
        acquisition_type=acquisition_type,
        acquisition_method=acquisition_method,
        min_value=min_value,
        max_value=max_value,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@router.get("/details")
def order_details(order_key: str = Query(..., min_length=1)):
    order = get_order_details(order_key)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
