from app.database.mongodb import procurement_collection


def fetch_order_details(
    order_key: str
):

    pipeline = [
        {
            "$match": {
                "order_key": order_key
            }
        },

        {
            "$group": {
                "_id": "$order_key",

                "purchase_order_number": {
                    "$first":
                        "$purchase_order_number"
                },

                "creation_date": {
                    "$first": "$creation_date"
                },

                "purchase_date": {
                    "$first": "$purchase_date"
                },

                "fiscal_year": {
                    "$first": "$fiscal_year"
                },

                "department_name": {
                    "$first": "$department_name"
                },

                "supplier_code": {
                    "$first": "$supplier_code"
                },

                "supplier_name": {
                    "$first": "$supplier_name"
                },

                "supplier_qualifications": {
                    "$first":
                        "$supplier_qualifications"
                },

                "supplier_zip_code": {
                    "$first":
                        "$supplier_zip_code"
                },

                "lpa_number": {
                    "$first": "$lpa_number"
                },

                "requisition_number": {
                    "$first":
                        "$requisition_number"
                },

                "acquisition_type": {
                    "$first":
                        "$acquisition_type"
                },

                "sub_acquisition_type": {
                    "$first":
                        "$sub_acquisition_type"
                },

                "acquisition_method": {
                    "$first":
                        "$acquisition_method"
                },

                "sub_acquisition_method": {
                    "$first":
                        "$sub_acquisition_method"
                },

                "calcard": {
                    "$first": "$calcard"
                },

                "total_value": {
                    "$sum": {
                        "$ifNull": [
                            "$total_price",
                            0
                        ]
                    }
                },

                "line_count": {
                    "$sum": 1
                },

                "items": {
                    "$push": {
                        "item_name":
                            "$item_name",

                        "item_description":
                            "$item_description",

                        "quantity":
                            "$quantity",

                        "unit_price":
                            "$unit_price",

                        "total_price":
                            "$total_price",

                        "classification_codes":
                            "$classification_codes",

                        "normalized_unspsc":
                            "$normalized_unspsc",

                        "commodity_title":
                            "$commodity_title",

                        "class":
                            "$class",

                        "class_title":
                            "$class_title",

                        "family":
                            "$family",

                        "family_title":
                            "$family_title",

                        "segment":
                            "$segment"
                    }
                }
            }
        },

        {
            "$project": {
                "_id": 0,
                "order_key": "$_id",
                "purchase_order_number": 1,
                "creation_date": 1,
                "purchase_date": 1,
                "fiscal_year": 1,
                "department_name": 1,
                "supplier_code": 1,
                "supplier_name": 1,
                "supplier_qualifications": 1,
                "supplier_zip_code": 1,
                "lpa_number": 1,
                "requisition_number": 1,
                "acquisition_type": 1,
                "sub_acquisition_type": 1,
                "acquisition_method": 1,
                "sub_acquisition_method": 1,
                "calcard": 1,
                "total_value": 1,
                "line_count": 1,
                "items": 1
            }
        }
    ]

    result = list(
        procurement_collection.aggregate(
            pipeline
        )
    )

    if not result:
        return None

    return result[0]
