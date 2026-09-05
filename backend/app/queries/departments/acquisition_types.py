from app.database.mongodb import procurement_collection


def fetch_department_acquisition_types(
    department: str
):
    pipeline = [
        {
            "$match": {
                "department_name":
                    department,

                "acquisition_type": {
                    "$nin": [
                        None,
                        ""
                    ]
                }
            }
        },

        {
            "$group": {
                "_id": {
                    "acquisition_type":
                        "$acquisition_type",

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
                }
            }
        },

        {
            "$group": {
                "_id":
                    "$_id.acquisition_type",

                "total_spending": {
                    "$sum":
                        "$order_total"
                },

                "unique_orders": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "total_spending": -1
            }
        },

        {
            "$project": {
                "_id": 0,

                "acquisition_type":
                    "$_id",

                "total_spending": 1,

                "unique_orders": 1
            }
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )