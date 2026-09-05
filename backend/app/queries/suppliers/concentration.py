from app.database.mongodb import procurement_collection


def fetch_supplier_concentration(
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

                "supplier_name": {
                    "$first": "$supplier_name"
                },

                "supplier_code": {
                    "$first": "$supplier_code"
                },

                "supplier_spend": {
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
            "$facet": {
                "overall": [
                    {
                        "$group": {
                            "_id": None,

                            "total_procurement_value": {
                                "$sum": "$supplier_spend"
                            },

                            "supplier_count": {
                                "$sum": 1
                            }
                        }
                    }
                ],

                "top_suppliers": [
                    {
                        "$sort": {
                            "supplier_spend": -1
                        }
                    },
                    {
                        "$limit": 10
                    }
                ]
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result or not result[0]["overall"]:
        return {
            "total_procurement_value": 0,
            "supplier_count": 0,
            "top_1_share": 0,
            "top_5_share": 0,
            "top_10_share": 0
        }

    data = result[0]

    overall = data["overall"][0]
    top_suppliers = data["top_suppliers"]

    total = overall["total_procurement_value"]

    top_1 = sum(
        supplier["supplier_spend"]
        for supplier in top_suppliers[:1]
    )

    top_5 = sum(
        supplier["supplier_spend"]
        for supplier in top_suppliers[:5]
    )

    top_10 = sum(
        supplier["supplier_spend"]
        for supplier in top_suppliers[:10]
    )

    def percentage(value):
        if not total:
            return 0

        return round(
            value / total * 100,
            2
        )

    return {
        "supplier_count":
            overall["supplier_count"],

        "total_procurement_value":
            total,

        "top_1_share":
            percentage(top_1),

        "top_5_share":
            percentage(top_5),

        "top_10_share":
            percentage(top_10)
    }