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


def main():

    questions = [
        (
            "How many orders were placed "
            "in Q2 2014?"
        ),

        
    ]

    for question in questions:

        print("\n" + "=" * 80)

        state = {
            "question": question,
            "retry_count": 0,
        }

        # 1. Generate
        state = generate_query(state)

        # 2. Validate
        state = validate_query(state)

        print("\nQUESTION:")
        print(question)

        print("\nPIPELINE:")
        pprint(
            state["pipeline"],
            sort_dicts=False,
        )

        print("\nVALID:")
        print(state["is_valid"])

        if not state["is_valid"]:

            print("\nVALIDATION ERROR:")
            print(
                state["validation_error"]
            )

            continue

        # 3. Execute
        state = execute_query(state)

        print("\nEXECUTION ERROR:")
        print(
            state["execution_error"]
        )

        print("\nRESULT COUNT:")
        print(
            state["result_count"]
        )

        print("\nMONGODB RESULT:")
        pprint(
            state["query_result"],
            sort_dicts=False,
        )


if __name__ == "__main__":
    main()