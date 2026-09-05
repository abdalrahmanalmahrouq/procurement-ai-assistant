from app.database.mongodb import procurement_collection


def fetch_department_ranking(
    limit: int = 10,
    year: int | None = None,
    quarter: int | None = None
):
    match_stage = {
        "department_name": {
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
                    "department_name":
                        "$department_name",

                    "order_key":
                        "$order_key"
                },

                "order_total": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                },

                "line_records": {
                    "$sum": 1
                }
            }
        },

        {
            "$group": {
                "_id":
                    "$_id.department_name",

                "total_procurement_value": {
                    "$sum": "$order_total"
                },

                "unique_orders": {
                    "$sum": 1
                },

                "line_records": {
                    "$sum": "$line_records"
                }
            }
        },

        {
            "$sort": {
                "total_procurement_value": -1
            }
        },

        {
            "$limit": limit
        },

        {
            "$project": {
                "_id": 0,

                "department_name": "$_id",

                "total_procurement_value": 1,

                "unique_orders": 1,

                "line_records": 1
            }
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )