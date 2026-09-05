from app.database.mongodb import procurement_collection


def fetch_number_of_suppliers(
    year: int | None = None,
    quarter: int | None = None
):
    match_stage = {
        "supplier_name": {
            "$nin": [None, ""]
        }
    }

    if year is not None:
        match_stage["year"] = year

    if quarter is not None:
        match_stage["quarter"] = quarter

    pipeline = [
        {
            "$match": match_stage
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {
                            "$and": [
                                {
                                    "$ne": [
                                        "$supplier_code",
                                        None
                                    ]
                                },
                                {
                                    "$ne": [
                                        "$supplier_code",
                                        ""
                                    ]
                                }
                            ]
                        },
                        "$supplier_code",
                        "$supplier_name"
                    ]
                }
            }
        },
        {
            "$count": "active_suppliers"
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return {
            "active_suppliers": 0
        }

    return {
        "active_suppliers":
            result[0]["active_suppliers"]
    }