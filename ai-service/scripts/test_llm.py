from app.ai.llm import get_llm


def main():

    llm = get_llm()

    response = llm.invoke(
        """
        You are going to work as a procurement
        analytics assistant.

        Reply with exactly one short sentence
        confirming that you are ready.
        """
    )

    print("\nLLM Response:")
    print(response.content)


if __name__ == "__main__":
    main()