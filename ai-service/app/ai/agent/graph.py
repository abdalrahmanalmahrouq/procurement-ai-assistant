import re

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

from app.ai.nodes.contextual_content import (
    contextual_content,
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

from app.ai.nodes.generate_visualization import (
    generate_visualization,
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
from app.ai.agent.report_graph import report_graph

MAX_QUERY_RETRIES = 1
checkpointer = InMemorySaver()


REPORT_INTENT = re.compile(
    r"\breport\b|\b(?:generate|create|prepare|build)\b.{0,100}"
    r"\b(?:pdf|procurement summary|briefing)\b",
    re.IGNORECASE,
)


def is_report_request(state: ProcurementAgentState) -> bool:
    return bool(
        state.get("report_spec_input")
        or REPORT_INTENT.search(state.get("question", ""))
    )


def route_after_classification(
    state: ProcurementAgentState,
) -> str:
    if state.get("route_category") == "analytical":
        if is_report_request(state):
            return "report"
        return "analytical"

    if state.get("route_category") == "contextual_content":
        return "contextual_content"

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


def route_after_answer(
    state: ProcurementAgentState,
) -> str:
    if (
        state.get("wants_visualization", False)
        and state.get("query_result")
        and not state.get("execution_error")
    ):
        return "visualize"

    return "save"


def route_after_contextual_content(
    state: ProcurementAgentState,
) -> str:
    if state.get("wants_visualization", False) and state.get("query_result"):
        return "visualize"

    return "save"


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
        "contextual_content",
        contextual_content,
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
        "generate_visualization",
        generate_visualization,
    )

    builder.add_node(
        "save_conversation",
        save_conversation,
    )

    builder.add_node("report_workflow", report_graph)

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
            "report": "report_workflow",
            "contextual_content": "contextual_content",
        },
    )

    builder.add_edge("report_workflow", "save_conversation")

    builder.add_edge(
        "generate_direct_response",
        "save_conversation",
    )

    builder.add_conditional_edges(
        "contextual_content",
        route_after_contextual_content,
        {
            "visualize": "generate_visualization",
            "save": "save_conversation",
        },
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

    builder.add_edge(
        "execute_query",
        "generate_answer",
    )

    # Answer generation owns the presentation decision. Visual requests
    # continue to the optional JSON node; ordinary answers are saved directly.
    builder.add_conditional_edges(
        "generate_answer",
        route_after_answer,
        {
            "visualize": "generate_visualization",
            "save": "save_conversation",
        },
    )

    builder.add_edge(
        "generate_visualization",
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
