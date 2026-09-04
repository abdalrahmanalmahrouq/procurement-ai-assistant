from app.database.mongodb import procurement_collection


def get_orders_by_quarter(year: int, quarter: int):

    pipeline = [
        {
            "$match": {
                "year": year,
                "quarter": quarter
            }
        },
        {
            "$group": {
                "_id": "$order_key"
            }
        },
        {
            "$count": "total_orders"
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return 0

    return result[0]["total_orders"]


def get_highest_spending_quarter():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": "$year",
                    "quarter": "$quarter"
                },
                "total_spending": {
                    "$sum": "$total_price"
                }
            }
        },
        {
            "$sort": {
                "total_spending": -1
            }
        },
        {
            "$limit": 1
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return None

    return {
        "year": result[0]["_id"]["year"],
        "quarter": result[0]["_id"]["quarter"],
        "total_spending": result[0]["total_spending"]
    }


def get_top_suppliers(limit: int = 10):
    pipeline = [
        {
            "$match": {
                "supplier_name": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": "$supplier_name",
                "total_procurement_value": {
                    "$sum": "$total_price"
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
        }
    ]

    results = list(
        procurement_collection.aggregate(pipeline)
    )

    return [
        {
            "supplier_name": row["_id"],
            "total_procurement_value":
                row["total_procurement_value"]
        }
        for row in results
    ]

def get_top_departments(limit: int = 10):
    pipeline = [
        {
            "$match": {
                "department_name": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": "$department_name",
                "total_spending": {
                    "$sum": "$total_price"
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

    results = list(
        procurement_collection.aggregate(pipeline)
    )

    return [
        {
            "department_name": row["_id"],
            "total_spending": row["total_spending"]
        }
        for row in results
    ]

def get_top_items(limit: int = 10):
    pipeline = [
        {
            "$match": {
                "item_name": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": "$item_name",
                "frequency": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "frequency": -1
            }
        },
        {
            "$limit": limit
        }
    ]

    results = list(
        procurement_collection.aggregate(pipeline)
    )

    return [
        {
            "item_name": row["_id"],
            "frequency": row["frequency"]
        }
        for row in results
    ]

def get_average_order_value():
    pipeline = [
        {
            "$group": {
                "_id": "$order_key",
                "order_total": {
                    "$sum": "$total_price"
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "average_order_value": {
                    "$avg": "$order_total"
                }
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return 0

    return result[0]["average_order_value"]