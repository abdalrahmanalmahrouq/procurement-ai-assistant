from pprint import pprint

from app.ai.nodes.generate_query import (
    generate_query,
)

from app.ai.nodes.validate_query import (
    validate_query,
)

from app.ai.nodes.execute_query import (
    execute_query,
)

from app.ai.nodes.generate_answer import (
    generate_answer,
)


def main():

    questions = [
        # (
        #     "How many orders were placed "
        #     "in Q2 2014?"
        # ),

        # (
        #     "Which quarter had the highest "
        #     "procurement spending?"
        # ),

        # (
        #     "Who were the top 5 suppliers "
        #     "by procurement value in 2014?"
        # ),

        # (
        #     "What were the 10 most "
        #     "frequently ordered items?"
        # ),

        (
            "Which department spent the most "
            "on IT Goods in Q3 2013?"
        ),
    ]

    for question in questions:

        print("\n" + "=" * 80)

        state = {
            "question": question,
            "retry_count": 0,
        }

        # 1. Generate MongoDB pipeline
        state = generate_query(state)

        # 2. Validate
        state = validate_query(state)

        if not state["is_valid"]:

            print("\nQUESTION:")
            print(question)

            print("\nVALIDATION ERROR:")
            print(
                state["validation_error"]
            )

            continue

        # 3. Execute against MongoDB
        state = execute_query(state)

        # 4. Generate user-facing answer
        state = generate_answer(state)

        print("\nQUESTION:")
        print(question)

        print("\nPIPELINE:")
        pprint(
            state["pipeline"],
            sort_dicts=False
        )

        print("\nRAW RESULT:")
        pprint(
            state["query_result"],
            sort_dicts=False
        )

        print("\nFINAL ANSWER:")
        print(
            state["answer"]
        )


if __name__ == "__main__":
    main()