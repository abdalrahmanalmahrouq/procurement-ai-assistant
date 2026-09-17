from pprint import pprint

from app.ai.agent.graph import (
    procurement_graph,
)


def main():

    question = (
        # "Which department spent the most "
        # "on IT Goods in Q3 2013?"
        (
            "Which quarter had the highest "
            "procurement spending?"
        ),
    )

    result = procurement_graph.invoke(
        {
            "question": question,
            "retry_count": 0,
        }
    )

    print("\n" + "=" * 80)

    print("\nQUESTION:")
    print(
        result["question"]
    )

    print("\nQUERY DESCRIPTION:")
    print(
        result.get(
            "query_description"
        )
    )

    print("\nPIPELINE:")
    pprint(
        result.get(
            "pipeline"
        ),
        sort_dicts=False,
    )

    print("\nVALID:")
    print(
        result.get(
            "is_valid"
        )
    )

    print("\nVALIDATION ERROR:")
    print(
        result.get(
            "validation_error"
        )
    )

    print("\nRAW RESULT:")
    pprint(
        result.get(
            "query_result"
        ),
        sort_dicts=False,
    )

    print("\nFINAL ANSWER:")
    print(
        result.get(
            "answer"
        )
    )


if __name__ == "__main__":
    main()