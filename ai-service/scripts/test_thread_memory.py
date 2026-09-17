from pprint import pprint

from app.ai.agent.graph import (
    procurement_graph,
)


def main():

    thread_id = "test-conversation-1"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }


    # ==========================================
    # QUESTION 1
    # ==========================================

    question_1 = (
        "Who were the top 5 suppliers "
        "by procurement value in 2014?"
    )

    result_1 = procurement_graph.invoke(
        {
            "question": question_1,
            "retry_count": 0,
        },
        config=config,
    )

    print("\n" + "=" * 80)
    print("\nQUESTION 1:")
    print(question_1)

    print("\nANSWER 1:")
    print(result_1["answer"])

    print("\nSAVED HISTORY:")
    pprint(
        result_1["chat_history"],
        sort_dicts=False,
    )


    # ==========================================
    # QUESTION 2 — FOLLOW-UP
    # ==========================================

    question_2 = "What about 2013?"

    result_2 = procurement_graph.invoke(
        {
            "question": question_2,
            "retry_count": 0,
        },
        config=config,
    )

    print("\n" + "=" * 80)
    print("\nQUESTION 2:")
    print(question_2)

    print("\nPIPELINE 2:")
    pprint(
        result_2["pipeline"],
        sort_dicts=False,
    )

    print("\nANSWER 2:")
    print(result_2["answer"])

    print("\nSAVED HISTORY:")
    pprint(
        result_2["chat_history"],
        sort_dicts=False,
    )


if __name__ == "__main__":
    main()