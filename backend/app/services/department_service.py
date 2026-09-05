from app.queries.departments.summary import (
    fetch_department_summary
)

from app.queries.departments.ranking import (
    fetch_department_ranking
)

from app.queries.departments.spend_trend import (
    fetch_department_spend_trend
)

from app.queries.departments.top_suppliers import (
    fetch_department_top_suppliers
)

from app.queries.departments.category_spend import (
    fetch_department_category_spend
)

from app.queries.departments.acquisition_types import (
    fetch_department_acquisition_types
)


def get_department_summary(
    year=None,
    quarter=None
):
    return fetch_department_summary(
        year,
        quarter
    )


def get_department_ranking(
    limit=10,
    year=None,
    quarter=None
):
    return fetch_department_ranking(
        limit,
        year,
        quarter
    )


def get_department_spend_trend(
    department,
    granularity="quarter"
):
    return fetch_department_spend_trend(
        department,
        granularity
    )


def get_department_top_suppliers(
    department,
    limit=10
):
    return fetch_department_top_suppliers(
        department,
        limit
    )


def get_department_category_spend(
    department,
    limit=10
):
    return fetch_department_category_spend(
        department,
        limit
    )


def get_department_acquisition_types(
    department
):
    return fetch_department_acquisition_types(
        department
    )