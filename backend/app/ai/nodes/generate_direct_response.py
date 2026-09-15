from app.ai.agent.state import ProcurementAgentState


DIRECT_RESPONSES = {
    "greeting": (
        "Hello! I'm your procurement analytics assistant. You can ask me "
        "about orders, spending, suppliers, departments, categories, or "
        "procurement trends."
    ),
    "project_help": (
        "I can answer questions about this procurement dataset by safely "
        "generating and running MongoDB aggregation queries. Try asking for "
        "order counts, total spending, top suppliers, department comparisons, "
        "category breakdowns, or trends by year, quarter, or month. I can also "
        "understand follow-up questions in the same conversation."
    ),
    "out_of_scope": (
        "I can only help with this project's procurement analytics and explain "
        "how to use the assistant. Please ask me about procurement orders, "
        "spending, suppliers, departments, categories, or time-based trends."
    ),
}


def generate_direct_response(
    state: ProcurementAgentState,
) -> ProcurementAgentState:
    route_category = state.get("route_category", "out_of_scope")

    return {
        **state,
        "answer": DIRECT_RESPONSES.get(
            route_category,
            DIRECT_RESPONSES["out_of_scope"],
        ),
    }
