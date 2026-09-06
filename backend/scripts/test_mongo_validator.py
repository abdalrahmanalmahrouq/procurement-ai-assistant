from pprint import pprint

from app.ai.validators.mongo_validator import (
    validate_pipeline,
)


def test_pipeline(
    name,
    pipeline
):

    valid, error = validate_pipeline(
        pipeline
    )

    print("\n" + "=" * 60)

    print(name)

    print("\nPipeline:")
    pprint(
        pipeline,
        sort_dicts=False
    )

    print("\nVALID:", valid)
    print("ERROR:", error)


def main():

    # -----------------------------------
    # Valid query
    # -----------------------------------

    test_pipeline(
        "Valid order count",

        [
            {
                "$match": {
                    "year": 2014,
                    "quarter": 2
                }
            },
            {
                "$group": {
                    "_id": "$order_key"
                }
            },
            {
                "$count": "total_orders"
            }
        ]
    )


    # -----------------------------------
    # Dangerous write operation
    # -----------------------------------

    test_pipeline(
        "Dangerous $out",

        [
            {
                "$match": {
                    "year": 2014
                }
            },
            {
                "$out":
                    "hacked_collection"
            }
        ]
    )


    # -----------------------------------
    # Invented field
    # -----------------------------------

    test_pipeline(
        "Unknown field",

        [
            {
                "$match": {
                    "approval_status":
                        "Approved"
                }
            }
        ]
    )


    # -----------------------------------
    # Excessive result limit
    # -----------------------------------

    test_pipeline(
        "Excessive limit",

        [
            {
                "$limit": 50000
            }
        ]
    )


    # -----------------------------------
    # Dangerous JavaScript
    # -----------------------------------

    test_pipeline(
        "Dangerous $function",

        [
            {
                "$project": {
                    "result": {
                        "$function": {
                            "body": "...",
                            "args": [],
                            "lang": "js"
                        }
                    }
                }
            }
        ]
    )


if __name__ == "__main__":
    main()