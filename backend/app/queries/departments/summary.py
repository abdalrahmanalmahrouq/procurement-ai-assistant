from app.database.mongodb import procurement_collection


def fetch_department_summary(
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

        # First reconstruct orders per department
        {
            "$group": {
                "_id": {
                    "department_name": "$department_name",
                    "order_key": "$order_key"
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

        # Aggregate at department level
        {
            "$group": {
                "_id": "$_id.department_name",

                "total_spending": {
                    "$sum": "$order_total"
                },

                "unique_orders": {
                    "$sum": 1
                }
            }
        },

        {
            "$facet": {

                "overall": [
                    {
                        "$group": {
                            "_id": None,

                            "department_count": {
                                "$sum": 1
                            },

                            "total_procurement_value": {
                                "$sum": "$total_spending"
                            },

                            "average_department_spend": {
                                "$avg": "$total_spending"
                            }
                        }
                    }
                ],

                "top_spending_department": [
                    {
                        "$sort": {
                            "total_spending": -1
                        }
                    },
                    {
                        "$limit": 1
                    }
                ],

                "most_orders_department": [
                    {
                        "$sort": {
                            "unique_orders": -1
                        }
                    },
                    {
                        "$limit": 1
                    }
                ]
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return {
            "department_count": 0,
            "total_procurement_value": 0,
            "average_department_spend": 0,
            "top_spending_department": None,
            "most_orders_department": None
        }

    raw = result[0]

    overall = (
        raw["overall"][0]
        if raw["overall"]
        else {}
    )

    top_department = (
        raw["top_spending_department"][0]
        if raw["top_spending_department"]
        else None
    )

    most_orders = (
        raw["most_orders_department"][0]
        if raw["most_orders_department"]
        else None
    )

    return {
        "department_count":
            overall.get(
                "department_count",
                0
            ),

        "total_procurement_value":
            overall.get(
                "total_procurement_value",
                0
            ),

        "average_department_spend":
            overall.get(
                "average_department_spend",
                0
            ),

        "top_spending_department": (
            {
                "department_name":
                    top_department["_id"],

                "total_spending":
                    top_department[
                        "total_spending"
                    ],

                "unique_orders":
                    top_department[
                        "unique_orders"
                    ]
            }
            if top_department
            else None
        ),

        "most_orders_department": (
            {
                "department_name":
                    most_orders["_id"],

                "unique_orders":
                    most_orders[
                        "unique_orders"
                    ],

                "total_spending":
                    most_orders[
                        "total_spending"
                    ]
            }
            if most_orders
            else None
        )
    }