from app.database.mongodb import procurement_collection


def fetch_department_category_spend(
    department: str,
    limit: int = 10
):
    pipeline = [
        {
            "$match": {
                "department_name":
                    department,

                "commodity_title": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },

        {
            "$group": {
                "_id":
                    "$commodity_title",

                "total_spending": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                },

                "order_keys": {
                    "$addToSet":
                        "$order_key"
                }
            }
        },

        {
            "$project": {
                "_id": 0,

                "category":
                    "$_id",

                "total_spending":
                    1,

                "unique_orders": {
                    "$size":
                        "$order_keys"
                }
            }
        },

        {
            "$sort": {
                "total_spending": -1
            }
        },

        {
            "$limit": limit
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )