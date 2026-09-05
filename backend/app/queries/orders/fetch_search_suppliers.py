from app.database.mongodb import procurement_collection

def fetch_search_suppliers(
    query: str,
    limit: int = 20
):

    pipeline = [
        {
            "$match": {
                "supplier_name": {
                    "$regex": query,
                    "$options": "i"
                }
            }
        },
        {
            "$group": {
                "_id": "$supplier_name"
            }
        },
        {
            "$sort": {
                "_id": 1
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
        result["_id"]
        for result in results
    ]
