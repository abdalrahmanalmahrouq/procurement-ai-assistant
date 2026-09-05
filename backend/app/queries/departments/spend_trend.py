from app.database.mongodb import procurement_collection


def fetch_department_spend_trend(
    department: str,
    granularity: str = "quarter"
):
    match_stage = {
        "department_name": department
    }

    if granularity == "month":
        period = {
            "year": "$_id.year",
            "month": "$_id.month"
        }

    else:
        period = {
            "year": "$_id.year",
            "quarter": "$_id.quarter"
        }

    pipeline = [
        {
            "$match": match_stage
        },

        # Reconstruct orders first
        {
            "$group": {
                "_id": {
                    "order_key":
                        "$order_key",

                    "year":
                        "$year",

                    "month":
                        "$month",

                    "quarter":
                        "$quarter"
                },

                "order_total": {
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
            "$group": {
                "_id": period,

                "total_spending": {
                    "$sum": "$order_total"
                },

                "unique_orders": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1,
                "_id.quarter": 1
            }
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )
