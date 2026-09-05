from app.database.mongodb import procurement_collection


def fetch_spend_over_time(
    granularity: str = "quarter",
    year: int | None = None
):
    match_stage = {}

    if year is not None:
        match_stage["year"] = year

    pipeline = []

    if match_stage:
        pipeline.append({
            "$match": match_stage
        })

    # First reconstruct purchase orders
    pipeline.append({
        "$group": {
            "_id": "$order_key",
            "order_total": {
                "$sum": {
                    "$ifNull": ["$total_price", 0]
                }
            },
            "year": {"$first": "$year"},
            "month": {"$first": "$month"},
            "quarter": {"$first": "$quarter"}
        }
    })

    if granularity == "year":
        group_id = {
            "year": "$year"
        }

    elif granularity == "month":
        group_id = {
            "year": "$year",
            "month": "$month"
        }

    else:
        group_id = {
            "year": "$year",
            "quarter": "$quarter"
        }

    pipeline.extend([
        {
            "$group": {
                "_id": group_id,
                "total_spending": {
                    "$sum": "$order_total"
                },
                "order_count": {
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
    ])

    return list(
        procurement_collection.aggregate(pipeline)
    )
