from app.database.mongodb import procurement_collection


def fetch_orders_summary():
    pipeline = [
        {
            "$group": {
                "_id": "$order_key",
                "order_total": {
                    "$sum": {
                        "$ifNull": ["$total_price", 0]
                    }
                },
                "line_count": {"$sum": 1},
                "purchase_order_number": {
                    "$first": "$purchase_order_number"
                },
                "department_name": {
                    "$first": "$department_name"
                },
                "supplier_name": {
                    "$first": "$supplier_name"
                },
                "creation_date": {
                    "$first": "$creation_date"
                }
            }
        },
        {
            "$facet": {
                "stats": [
                    {
                        "$group": {
                            "_id": None,
                            "total_orders": {"$sum": 1},
                            "total_line_records": {
                                "$sum": "$line_count"
                            },
                            "total_procurement_value": {
                                "$sum": "$order_total"
                            },
                            "average_order_value": {
                                "$avg": "$order_total"
                            }
                        }
                    }
                ],
                "largest_order": [
                    {
                        "$sort": {
                            "order_total": -1
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
    )[0]

    stats = result["stats"][0] if result["stats"] else {}

    largest = (
        result["largest_order"][0]
        if result["largest_order"]
        else None
    )

    return {
        "total_orders": stats.get("total_orders", 0),
        "total_line_records":
            stats.get("total_line_records", 0),
        "total_procurement_value":
            stats.get("total_procurement_value", 0),
        "average_order_value":
            stats.get("average_order_value", 0),
        "largest_order": largest
    }
