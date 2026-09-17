from pprint import pprint

from app.ai.nodes.generate_query import (
    generate_query,
)

from app.ai.nodes.validate_query import (
    validate_query,
)


def main():

    questions = [
        (
            "How many orders were "
            "placed in Q2 2014?"
        ),

        (
            "Which department spent "
            "the most on IT Goods "
            "in Q3 2013?"
        ),

        (
            "Who were the top 5 "
            "suppliers in 2014?"
        ),
    ]

    for question in questions:

        print("\n" + "=" * 70)

        state = {
            "question": question,
            "retry_count": 0,
        }

        # Generate
        state = generate_query(
            state
        )

        # Validate
        state = validate_query(
            state
        )

        print("\nQUESTION:")
        print(question)

        print("\nPIPELINE:")
        pprint(
            state["pipeline"],
            sort_dicts=False
        )

        print("\nVALID:")
        print(
            state["is_valid"]
        )

        print("\nVALIDATION ERROR:")
        print(
            state["validation_error"]
        )


if __name__ == "__main__":
    main()