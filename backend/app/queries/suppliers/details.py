from app.database.mongodb import procurement_collection


def fetch_supplier_details(
    supplier_code: str
):
    supplier_codes: list[str | int | float] = [supplier_code]

    try:
        numeric_code = float(supplier_code)
        supplier_codes.append(numeric_code)

        if numeric_code.is_integer():
            supplier_codes.append(int(numeric_code))
    except ValueError:
        pass

    pipeline = [
        {
            "$match": {
                "supplier_code": {
                    "$in": supplier_codes
                }
            }
        },

        {
            "$facet": {

                # ----------------------------------
                # Basic supplier information
                # ----------------------------------

                "supplier": [
                    {
                        "$limit": 1
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "supplier_code": 1,
                            "supplier_name": 1,
                            "supplier_zip_code": 1,
                            "supplier_qualifications": 1
                        }
                    }
                ],

                # ----------------------------------
                # Order-level statistics
                # ----------------------------------

                "summary": [
                    {
                        "$group": {
                            "_id": "$order_key",

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
                            "_id": None,

                            "unique_orders": {
                                "$sum": 1
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

                # ----------------------------------
                # Raw line-record count
                # ----------------------------------

                "records": [
                    {
                        "$count": "line_records"
                    }
                ],

                # ----------------------------------
                # Departments buying from supplier
                # ----------------------------------

                "departments": [
                    {
                        "$group": {
                            "_id":
                                "$department_name",

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
                    },

                    {
                        "$limit": 10
                    }
                ],

                # ----------------------------------
                # Top commodities/categories
                # ----------------------------------

                "categories": [
                    {
                        "$match": {
                            "commodity_title": {
                                "$nin": [
                                    None,
                                    ""
                                ]
                            }
                        }
                    },

                    {
                        "$group": {
                            "_id":
                                "$commodity_title",

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
                    },

                    {
                        "$limit": 10
                    }
                ],

                # ----------------------------------
                # Quarterly supplier spend trend
                # ----------------------------------

                "spend_trend": [
                    {
                        "$group": {
                            "_id": {
                                "year": "$year",
                                "quarter": "$quarter"
                            },

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
                            "_id.year": 1,
                            "_id.quarter": 1
                        }
                    }
                ]
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(pipeline)
    )

    if not result:
        return None

    raw = result[0]

    if not raw["supplier"]:
        return None

    summary = (
        raw["summary"][0]
        if raw["summary"]
        else {}
    )

    line_records = (
        raw["records"][0]["line_records"]
        if raw["records"]
        else 0
    )

    return {
        "supplier": raw["supplier"][0],

        "summary": {
            "unique_orders":
                summary.get(
                    "unique_orders",
                    0
                ),

            "total_procurement_value":
                summary.get(
                    "total_procurement_value",
                    0
                ),

            "average_order_value":
                summary.get(
                    "average_order_value",
                    0
                ),

            "line_records":
                line_records
        },

        "departments":
            raw["departments"],

        "top_categories":
            raw["categories"],

        "spend_trend":
            raw["spend_trend"]
    }
