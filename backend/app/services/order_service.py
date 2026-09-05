import re

from app.database.mongodb import procurement_collection
from app.queries.orders import (
                        fetch_orders_summary,
                        fetch_spend_over_time,
                        fetch_acquisition_type_breakdown,
                        fetch_order_value_distribution,
                        fetch_order_filter_options,
                        fetch_search_suppliers,
                        fetch_orders,
                        fetch_order_details)

def get_orders_summary():
    return fetch_orders_summary()

def get_spend_over_time(granularity: str = "quarter",
    year: int | None = None):
    return fetch_spend_over_time(
        granularity=granularity,
        year=year
    )


def get_acquisition_type_breakdown(
    year: int | None = None
):
    return fetch_acquisition_type_breakdown(year=year)

def get_order_value_distribution():
    return fetch_order_value_distribution()


def get_order_filter_options():
    return fetch_order_filter_options()
    

def search_suppliers(
    query: str,
    limit: int = 20
):
    return fetch_search_suppliers(query, limit)

def get_orders(
    page: int = 1,
    page_size: int = 20,
    year: int | None = None,
    quarter: int | None = None,
    fiscal_year: str | None = None,
    department: str | None = None,
    supplier: str | None = None,
    acquisition_type: str | None = None,
    acquisition_method: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    search: str | None = None,
    sort_by: str = "creation_date",
    sort_direction: str = "desc"
):
   return fetch_orders(
    page,
    page_size,
    year,
    quarter,
    fiscal_year,
    department,
    supplier,
    acquisition_type,
    acquisition_method,
    min_value,
    max_value,
    search,
    sort_by,
    sort_direction,
)

def get_order_details(
    order_key: str
):
    return fetch_order_details(order_key=order_key)