from typing import Literal

from fastapi import (
    APIRouter,
    Query
)

from app.services.department_service import (
    get_department_summary,
    get_department_ranking,
    get_department_spend_trend,
    get_department_top_suppliers,
    get_department_category_spend,
    get_department_acquisition_types
)


router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"]
)

@router.get("/summary")
def department_summary(
    year: int | None = None,

    quarter: int | None = Query(
        default=None,
        ge=1,
        le=4
    )
):
    return get_department_summary(
        year,
        quarter
    )

@router.get("/ranking")
def department_ranking(
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
    return get_department_ranking(
        limit,
        year,
        quarter
    )

@router.get("/spend-trend")
def department_spend_trend(
    department: str,

    granularity: Literal[
        "month",
        "quarter"
    ] = "quarter"
):
    return get_department_spend_trend(
        department,
        granularity
    )

@router.get("/top-suppliers")
def department_top_suppliers(
    department: str,

    limit: int = Query(
        default=10,
        ge=1,
        le=50
    )
):
    return get_department_top_suppliers(
        department,
        limit
    )

@router.get("/category-spend")
def department_category_spend(
    department: str,

    limit: int = Query(
        default=10,
        ge=1,
        le=50
    )
):
    return get_department_category_spend(
        department,
        limit
    )

@router.get("/acquisition-types")
def department_acquisition_types(
    department: str
):
    return get_department_acquisition_types(
        department
    )