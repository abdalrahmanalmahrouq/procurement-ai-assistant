from app.database.mongodb import procurement_collection


def fetch_average_supplier_spend(
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

        # Calculate spend for each supplier
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
                },

                "supplier_spend": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                }
            }
        },

        # Average all supplier totals
        {
            "$group": {
                "_id": None,

                "average_supplier_spend": {
                    "$avg": "$supplier_spend"
                },

                "supplier_count": {
                    "$sum": 1
                }
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return {
            "average_supplier_spend": 0,
            "supplier_count": 0
        }

    return {
        "average_supplier_spend":
            result[0]["average_supplier_spend"],

        "supplier_count":
            result[0]["supplier_count"]
    }