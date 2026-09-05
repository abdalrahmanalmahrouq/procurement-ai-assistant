from app.database.mongodb import procurement_collection


def fetch_category_spend(
    year: int | None = None,
    quarter: int | None = None,
    top_n: int = 5
):
    match_stage = {
        "commodity_title": {
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
                "_id": "$commodity_title",

                "total_spending": {
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
            "$sort": {
                "total_spending": -1
            }
        }
    ]

    categories = list(
        procurement_collection.aggregate(pipeline)
    )

    if not categories:
        return []

    top_categories = categories[:top_n]
    remaining_categories = categories[top_n:]

    result = [
        {
            "category": category["_id"],
            "total_spending":
                category["total_spending"]
        }
        for category in top_categories
    ]

    other_total = sum(
        category["total_spending"]
        for category in remaining_categories
    )

    if other_total != 0:
        result.append({
            "category": "Other",
            "total_spending": other_total
        })

    return result