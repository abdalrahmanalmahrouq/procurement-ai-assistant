from pprint import pprint

from app.ai.agent.graph import (
    procurement_graph,
)


def main():

    history = []

    # =================================
    # FIRST QUESTION
    # =================================

    question_1 = (
        "Which quarter had the highest "
        "procurement spending?"
    )

    result_1 = procurement_graph.invoke(
        {
            "question": question_1,
            "chat_history": history,
            "retry_count": 0,
        }
    )

    print("\n" + "=" * 80)

    print("\nFIRST QUESTION:")
    print(question_1)

    print("\nFIRST PIPELINE:")
    pprint(
        result_1["pipeline"],
        sort_dicts=False
    )

    print("\nFIRST ANSWER:")
    print(
        result_1["answer"]
    )


    # =================================
    # SAVE FIRST CONVERSATION
    # =================================

    history.append(
        {
            "role": "user",
            "content": question_1
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": result_1["answer"]
        }
    )


    # =================================
    # FOLLOW-UP QUESTION
    # =================================

    question_2 = (
        "What about the second highest?"
    )

    result_2 = procurement_graph.invoke(
        {
            "question": question_2,
            "chat_history": history,
            "retry_count": 0,
        }
    )

    print("\n" + "=" * 80)

    print("\nFOLLOW-UP QUESTION:")
    print(question_2)

    print("\nFOLLOW-UP PIPELINE:")
    pprint(
        result_2["pipeline"],
        sort_dicts=False
    )

    print("\nFOLLOW-UP ANSWER:")
    print(
        result_2["answer"]
    )


if __name__ == "__main__":
    main()