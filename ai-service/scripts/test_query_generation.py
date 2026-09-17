from pprint import pprint

from app.ai.nodes.generate_query import (
    generate_query,
)


def main():

    questions = [
        "How many orders were placed in Q2 2014?",

        "Which quarter had the highest procurement spending?",

        "Who were the top 5 suppliers by procurement value in 2014?",

        "What were the 10 most frequently ordered items?",

        (
            "Which department spent the most "
            "on IT Goods in Q3 2013?"
        ),
    ]

    for question in questions:

        print("\n" + "=" * 70)

        result = generate_query({
            "question": question,
            "retry_count": 0,
        })

        print("\nQUESTION:")
        print(question)

        print("\nDESCRIPTION:")
        print(
            result["query_description"]
        )

        print("\nPIPELINE:")

        pprint(
            result["pipeline"],
            sort_dicts=False
        )


if __name__ == "__main__":
    main()