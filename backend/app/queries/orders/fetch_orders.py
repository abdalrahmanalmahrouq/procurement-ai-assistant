from app.database.mongodb import procurement_collection


def fetch_orders(
    page: int = 1,
    page_size: int = 20,
    year: int | None = None,
    quarter: int | None = None,
    fiscal_year: str | None = None,
    department: str | None = None,
    supplier: str | None = None,
    acquisition_type: str | None = None,
    acquisition_method: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    search: str | None = None,
    sort_by: str = "creation_date",
    sort_direction: str = "desc"
):
    pre_match = {}

    if year is not None:
        pre_match["year"] = year
    if quarter is not None:
        pre_match["quarter"] = quarter
    if fiscal_year:
        pre_match["fiscal_year"] = fiscal_year
    if department:
        pre_match["department_name"] = department
    if supplier:
        pre_match["supplier_name"] = supplier
    if acquisition_type:
        pre_match["acquisition_type"] = acquisition_type
    if acquisition_method:
        pre_match["acquisition_method"] = acquisition_method

    if search:
        search_pattern = re.escape(search)
        pre_match["$or"] = [
            {"purchase_order_number": {"$regex": search_pattern, "$options": "i"}},
            {"supplier_name": {"$regex": search_pattern, "$options": "i"}},
            {"department_name": {"$regex": search_pattern, "$options": "i"}},
            {"item_name": {"$regex": search_pattern, "$options": "i"}},
        ]

    base_pipeline = []
    if pre_match:
        base_pipeline.append({"$match": pre_match})

    # Keep the first pass lightweight. Grouping all item names before pagination
    # exceeds MongoDB's aggregation memory limit on the complete dataset.
    base_pipeline.append({
        "$group": {
            "_id": "$order_key",
            "purchase_order_number": {"$first": "$purchase_order_number"},
            "creation_date": {"$max": "$creation_date"},
            "line_count": {"$sum": 1},
            "total_value": {"$sum": {"$ifNull": ["$total_price", 0]}},
        }
    })

    value_match = {}
    if min_value is not None:
        value_match.setdefault("total_value", {})["$gte"] = min_value
    if max_value is not None:
        value_match.setdefault("total_value", {})["$lte"] = max_value

    filtered_pipeline = list(base_pipeline)
    if value_match:
        filtered_pipeline.append({"$match": value_match})

    count_result = list(procurement_collection.aggregate(
        [*filtered_pipeline, {"$count": "total"}],
        allowDiskUse=True,
    ))
    total = count_result[0]["total"] if count_result else 0

    allowed_sort_fields = {
        "creation_date": "creation_date",
        "total_value": "total_value",
        "line_count": "line_count",
        "purchase_order_number": "purchase_order_number",
    }
    mongo_sort_field = allowed_sort_fields.get(sort_by, "creation_date")
    mongo_sort_direction = -1 if sort_direction == "desc" else 1
    skip = (page - 1) * page_size

    selected_orders = list(procurement_collection.aggregate(
        [
            *filtered_pipeline,
            {"$sort": {mongo_sort_field: mongo_sort_direction, "_id": 1}},
            {"$skip": skip},
            {"$limit": page_size},
            {"$project": {"_id": 0, "order_key": "$_id"}},
        ],
        allowDiskUse=True,
    ))
    order_keys = [order["order_key"] for order in selected_orders]

    if not order_keys:
        orders = []
    else:
        hydrated_orders = list(procurement_collection.aggregate([
            {"$match": {"order_key": {"$in": order_keys}}},
            {
                "$group": {
                    "_id": "$order_key",
                    "purchase_order_number": {"$first": "$purchase_order_number"},
                    "creation_date": {"$max": "$creation_date"},
                    "purchase_date": {"$first": "$purchase_date"},
                    "fiscal_year": {"$first": "$fiscal_year"},
                    "department_name": {"$first": "$department_name"},
                    "supplier_name": {"$first": "$supplier_name"},
                    "acquisition_type": {"$first": "$acquisition_type"},
                    "acquisition_method": {"$first": "$acquisition_method"},
                    "line_count": {"$sum": 1},
                    "total_value": {"$sum": {"$ifNull": ["$total_price", 0]}},
                    "item_names": {"$addToSet": "$item_name"},
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
                    "supplier_name": 1,
                    "acquisition_type": 1,
                    "acquisition_method": 1,
                    "line_count": 1,
                    "total_value": 1,
                    "items_preview": {"$slice": ["$item_names", 3]},
                }
            },
        ], allowDiskUse=True))
        orders_by_key = {order["order_key"]: order for order in hydrated_orders}
        orders = [orders_by_key[key] for key in order_keys if key in orders_by_key]

    return {
        "page": page,
        "page_size": page_size,
        "total_orders": total,
        "total_pages": (total + page_size - 1) // page_size,
        "orders": orders,
    }
