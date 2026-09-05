from app.queries.suppliers.concentration import (fetch_supplier_concentration,)
from app.queries.suppliers.details import (fetch_supplier_details)
from app.queries.suppliers.number_of_suppliers import (fetch_number_of_suppliers)
from app.queries.suppliers.top_supplier import (fetch_top_supplier)
from app.queries.suppliers.total_procurement_value import (fetch_total_procurement_value)
from app.queries.suppliers.average_supplier_spend import (fetch_average_supplier_spend)
from app.queries.suppliers.top_suppliers import (fetch_top_suppliers)
from app.queries.suppliers.category_spend import (fetch_category_spend)
def get_supplier_concentration(
    year=None,
    quarter=None
):
    return fetch_supplier_concentration(
        year=year,
        quarter=quarter
    )

def get_supplier_details(
    supplier_code: str
):
    return fetch_supplier_details(
        supplier_code
    )

def get_number_of_suppliers(
    year=None,
    quarter=None
):
    return fetch_number_of_suppliers(
        year,
        quarter
    )


def get_top_supplier(
    year=None,
    quarter=None
):
    return fetch_top_supplier(
        year,
        quarter
    )


def get_total_procurement_value(
    year=None,
    quarter=None
):
    return fetch_total_procurement_value(
        year,
        quarter
    )


def get_average_supplier_spend(
    year=None,
    quarter=None
):
    return fetch_average_supplier_spend(
        year,
        quarter
    )


def get_top_suppliers(
    limit=10,
    year=None,
    quarter=None
):
    return fetch_top_suppliers(
        limit,
        year,
        quarter
    )


def get_category_spend(
    year=None,
    quarter=None,
    top_n=5
):
    return fetch_category_spend(
        year,
        quarter,
        top_n
    )