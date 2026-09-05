from app.database.mongodb import procurement_collection


def fetch_department_top_suppliers(
    department: str,
    limit: int = 10
):
    pipeline = [
        {
            "$match": {
                "department_name": department,

                "supplier_name": {
                    "$nin": [None, ""]
                }
            }
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
                    "$first":
                        "$supplier_code"
                },

                "supplier_name": {
                    "$first":
                        "$supplier_name"
                },

                "total_spending": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                },

                "orders": {
                    "$addToSet":
                        "$order_key"
                }
            }
        },

        {
            "$project": {
                "_id": 0,

                "supplier_code": 1,

                "supplier_name": 1,

                "total_spending": 1,

                "unique_orders": {
                    "$size": "$orders"
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