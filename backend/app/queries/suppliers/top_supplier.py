from app.database.mongodb import procurement_collection


def fetch_top_supplier(
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
                },

                "supplier_code": {
                    "$first": "$supplier_code"
                },

                "supplier_name": {
                    "$first": "$supplier_name"
                },

                "total_procurement_value": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {
                "total_procurement_value": -1
            }
        },
        {
            "$limit": 1
        },
        {
            "$project": {
                "_id": 0,
                "supplier_code": 1,
                "supplier_name": 1,
                "total_procurement_value": 1
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return None

    return result[0]