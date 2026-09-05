from app.database.mongodb import procurement_collection

def fetch_order_filter_options():

    fiscal_years = sorted(
        procurement_collection.distinct(
            "fiscal_year"
        )
    )

    acquisition_types = sorted(
        value
        for value in procurement_collection.distinct(
            "acquisition_type"
        )
        if value
    )

    acquisition_methods = sorted(
        value
        for value in procurement_collection.distinct(
            "acquisition_method"
        )
        if value
    )

    departments = sorted(
        value
        for value in procurement_collection.distinct(
            "department_name"
        )
        if value
    )

    return {
        "fiscal_years": fiscal_years,
        "acquisition_types": acquisition_types,
        "acquisition_methods": acquisition_methods,
        "departments": departments
    }
