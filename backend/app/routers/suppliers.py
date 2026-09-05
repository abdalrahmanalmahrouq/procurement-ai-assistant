from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from app.services.supplier_service import (
    get_supplier_concentration,
    get_supplier_details,
    get_number_of_suppliers,
    get_top_supplier,
    get_total_procurement_value,
    get_average_supplier_spend,
    get_top_suppliers,
    get_category_spend
)
router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

@router.get("/concentration")
def supplier_concentration(
    year: int | None = None,
    quarter: int | None = None
):
    return get_supplier_concentration(
        year=year,
        quarter=quarter
    )

@router.get("/details")
def supplier_details(
    supplier_code: str
):

    supplier = get_supplier_details(
        supplier_code
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    return supplier

@router.get("/number-of-suppliers")
def number_of_suppliers(
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_number_of_suppliers(
        year,
        quarter
    )

@router.get("/top")
def top_supplier(
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_top_supplier(
        year,
        quarter
    )

@router.get("/total-value")
def total_procurement_value(
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_total_procurement_value(
        year,
        quarter
    )

@router.get("/average-spend")
def average_supplier_spend(
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_average_supplier_spend(
        year,
        quarter
    )

@router.get("/ranking")
def supplier_ranking(
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_top_suppliers(
        limit,
        year,
        quarter
    )

@router.get("/category-spend")
def category_spend(
    year: int | None = None,
    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    ),
    top_n: int = Query(
        default=5,
        ge=1,
        le=10
    )
):
    return get_category_spend(
        year,
        quarter,
        top_n
    )
