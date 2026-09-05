from app.database.mongodb import procurement_collection


def fetch_acquisition_type_breakdown(
    year: int | None = None
):
    match_stage = {
        "acquisition_type": {
            "$nin": [None, ""]
        }
    }

    if year is not None:
        match_stage["year"] = year

    pipeline = [
        {
            "$match": match_stage
        },

        # One row per order + acquisition type
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

                "total_procurement_value": {
                    "$sum": "$order_total"
                },

                "unique_orders": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "total_procurement_value": -1
            }
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )
