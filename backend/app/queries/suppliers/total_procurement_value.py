from app.database.mongodb import procurement_collection


def fetch_total_procurement_value(
    year: int | None = None,
    quarter: int | None = None
):
    match_stage = {}

    if year is not None:
        match_stage["year"] = year

    if quarter is not None:
        match_stage["quarter"] = quarter

    pipeline = []

    if match_stage:
        pipeline.append({
            "$match": match_stage
        })

    pipeline.append({
        "$group": {
            "_id": None,

            "total_procurement_value": {
                "$sum": {
                    "$ifNull": [
                        "$total_price",
                        0
                    ]
                }
            }
        }
    })

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return {
            "total_procurement_value": 0
        }

    return {
        "total_procurement_value":
            result[0]["total_procurement_value"]
    }