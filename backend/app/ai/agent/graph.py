from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.checkpoint.memory import (
    InMemorySaver,
)


from app.ai.agent.state import (
    ProcurementAgentState,
)

from app.ai.nodes.generate_query import (
    generate_query,
)

from app.ai.nodes.route_question import (
    route_question,
)

from app.ai.nodes.generate_direct_response import (
    generate_direct_response,
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

from app.ai.nodes.correct_query import (
    correct_query,
)

from app.ai.nodes.handle_validation_failure import (
    handle_validation_failure,
)

from app.ai.nodes.save_conversation import (
    save_conversation,
)

MAX_QUERY_RETRIES = 2
checkpointer = InMemorySaver()


def route_after_classification(
    state: ProcurementAgentState,
) -> str:
    if state.get("route_category") == "analytical":
        return "analytical"

    return "direct"

def route_after_validation(
    state: ProcurementAgentState
) -> str:

    # Query passed validation
    if state.get("is_valid", False):
        return "execute"

    retry_count = state.get(
        "retry_count",
        0
    )

    # Query failed but we can retry
    if retry_count < MAX_QUERY_RETRIES:
        return "retry"

    # Too many failed attempts
    return "failed"

def build_procurement_graph():

    builder = StateGraph(
        ProcurementAgentState
    )

    # -----------------------------
    # Register nodes
    # -----------------------------

    builder.add_node(
        "route_question",
        route_question,
    )

    builder.add_node(
        "generate_direct_response",
        generate_direct_response,
    )

    builder.add_node(
        "generate_query",
        generate_query,
    )

    builder.add_node(
        "validate_query",
        validate_query,
    )

    builder.add_node(
        "execute_query",
        execute_query,
    )

    builder.add_node(
        "correct_query",
        correct_query,
    )

    builder.add_node(
        "validation_failure",
        handle_validation_failure,
    )

    builder.add_node(
        "generate_answer",
        generate_answer,
    )

    builder.add_node(
        "save_conversation",
        save_conversation,
    )

    # -----------------------------
    # Define workflow
    # -----------------------------

    builder.add_edge(
        START,
        "route_question",
    )

    builder.add_conditional_edges(
        "route_question",
        route_after_classification,
        {
            "direct": "generate_direct_response",
            "analytical": "generate_query",
        },
    )

    builder.add_edge(
        "generate_direct_response",
        "save_conversation",
    )

    builder.add_edge(
        "generate_query",
        "validate_query",
    )

    builder.add_conditional_edges(
        "validate_query",

        route_after_validation,

        {
            "execute":
                "execute_query",

            "retry":
                "correct_query",

            "failed":
                "validation_failure",
        },
    )

    # Retry loop
    builder.add_edge(
        "correct_query",
        "validate_query",
    )

    # Successful execution
    builder.add_edge(
        "execute_query",
        "generate_answer",
    )

    builder.add_edge(
        "generate_answer",
        "save_conversation",
    )

    builder.add_edge(
        "save_conversation",
        END,
    )

    # Failed after retries
    builder.add_edge(
        "validation_failure",
        "save_conversation",
    )

    # -----------------------------
    # Compile graph
    # -----------------------------

    return builder.compile(
        checkpointer=checkpointer
    )


procurement_graph = (
    build_procurement_graph()
)
