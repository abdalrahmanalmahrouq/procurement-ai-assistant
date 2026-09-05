from app.database.mongodb import procurement_collection


def fetch_top_suppliers(
    limit: int = 10,
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
                    "supplier": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$supplier_code", None]},
                                    {"$ne": ["$supplier_code", ""]}
                                ]
                            },
                            "$supplier_code",
                            "$supplier_name"
                        ]
                    },
                    "order_key": "$order_key"
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
                },
                "line_records": {
                    "$sum": 1
                }
            }
        },

        {
            "$group": {
                "_id": "$_id.supplier",
                "supplier_code": {"$first": "$supplier_code"},
                "supplier_name": {"$first": "$supplier_name"},
                "total_procurement_value": {
                    "$sum": "$total_procurement_value"
                },
                "unique_orders": {"$sum": 1},
                "line_records": {"$sum": "$line_records"}
            }
        },

        {
            "$project": {
                "_id": 0,

                "supplier_code": 1,
                "supplier_name": 1,
                "total_procurement_value": 1,
                "line_records": 1,
                "unique_orders": 1
            }
        },

        {
            "$sort": {
                "total_procurement_value": -1
            }
        },

        {
            "$limit": limit
        }
    ]

    return list(
        procurement_collection.aggregate(
            pipeline,
            allowDiskUse=True
        )
    )
