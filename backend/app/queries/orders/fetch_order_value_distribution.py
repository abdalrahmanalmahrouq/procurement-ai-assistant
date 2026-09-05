from app.database.mongodb import procurement_collection


def fetch_order_value_distribution():

    pipeline = [
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
            "$project": {
                "order_total": 1,

                "bucket": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {
                                    "$lt": [
                                        "$order_total",
                                        0
                                    ]
                                },
                                "then": "Negative"
                            },
                            {
                                "case": {
                                    "$lt": [
                                        "$order_total",
                                        5000
                                    ]
                                },
                                "then": "Under $5K"
                            },
                            {
                                "case": {
                                    "$lt": [
                                        "$order_total",
                                        25000
                                    ]
                                },
                                "then": {
                                    "$literal": "$5K-$25K"
                                }
                            },
                            {
                                "case": {
                                    "$lt": [
                                        "$order_total",
                                        100000
                                    ]
                                },
                                "then": {
                                    "$literal": "$25K-$100K"
                                }
                            },
                            {
                                "case": {
                                    "$lt": [
                                        "$order_total",
                                        500000
                                    ]
                                },
                                "then": {
                                    "$literal": "$100K-$500K"
                                }
                            }
                        ],

                        "default": {
                            "$literal": "$500K+"
                        }
                    }
                }
            }
        },

        {
            "$group": {
                "_id": "$bucket",

                "orders": {
                    "$sum": 1
                },

                "total_value": {
                    "$sum": "$order_total"
                }
            }
        }
    ]

    return list(
        procurement_collection.aggregate(pipeline)
    )
