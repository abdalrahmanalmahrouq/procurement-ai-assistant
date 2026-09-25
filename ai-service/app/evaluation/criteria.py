"""Deterministic LangSmith evaluators for agent behavior."""

from __future__ import annotations

from typing import Any

from app.ai.validators.mongo_validator import validate_pipeline


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _outputs(run: Any) -> dict[str, Any]:
    outputs = _value(run, "outputs", {})
    return outputs if isinstance(outputs, dict) else {}


def _reference_outputs(example: Any) -> dict[str, Any]:
    outputs = _value(example, "outputs", {})
    return outputs if isinstance(outputs, dict) else {}


def _turns(run: Any) -> list[dict[str, Any]]:
    turns = _outputs(run).get("turns", [])
    return turns if isinstance(turns, list) else []


def _run_error(run: Any) -> str | None:
    error = _outputs(run).get("error") or _value(run, "error")
    return str(error) if error else None


def _feedback(key: str, score: bool | float, comment: str) -> dict[str, object]:
    return {"key": key, "score": score, "comment": comment}


def _pipeline_fields(pipeline: Any) -> set[str]:
    fields: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key.startswith("$") and key[1:] in {"sum", "avg", "min", "max", "first", "last"}:
                    visit(nested)
                    continue
                if not key.startswith("$") and key not in {"_id"}:
                    fields.add(key)
                visit(nested)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and value.startswith("$"):
            fields.add(value[1:].split(".", 1)[0])

    visit(pipeline)
    return fields


def route_accuracy(run: Any, example: Any) -> dict[str, object]:
    """Check every route in a multi-turn example, not only its final turn."""
    if error := _run_error(run):
        return _feedback("routing_accuracy", False, f"Target function failed: {error}")

    expected = _reference_outputs(example).get("expected_routes", [])
    actual = [turn.get("route_category") for turn in _turns(run)]
    passed = actual == expected
    return _feedback(
        "routing_accuracy",
        passed,
        f"expected routes={expected}; actual routes={actual}",
    )


def mongodb_query_validity(run: Any, example: Any) -> dict[str, object]:
    """Require every analytical turn to produce a valid, executable pipeline."""
    if error := _run_error(run):
        return _feedback(
            "mongodb_query_validity",
            False,
            f"Target function failed: {error}",
        )

    expected_routes = _reference_outputs(example).get("expected_routes", [])
    analytical_turns = [
        turn for turn, route in zip(_turns(run), expected_routes)
        if route == "analytical"
    ]
    failures: list[str] = []
    for index, turn in enumerate(analytical_turns, start=1):
        pipeline = turn.get("pipeline")
        valid, error = validate_pipeline(pipeline)
        if not valid or not turn.get("is_valid"):
            failures.append(f"turn {index}: {error or turn.get('validation_error')}")
    return _feedback(
        "mongodb_query_validity",
        not failures,
        "; ".join(failures) or "Every analytical pipeline passed deterministic validation.",
    )


def analytical_correctness(run: Any, example: Any) -> dict[str, object]:
    """Check required business fields, successful execution, and a usable answer."""
    if error := _run_error(run):
        return _feedback(
            "analytical_correctness",
            False,
            f"Target function failed: {error}",
        )

    expectations = _reference_outputs(example)
    required_by_turn = expectations.get("required_pipeline_fields", [])
    expected_routes = expectations.get("expected_routes", [])
    failures: list[str] = []

    for index, (turn, route) in enumerate(zip(_turns(run), expected_routes)):
        if route != "analytical":
            continue
        if turn.get("execution_error"):
            failures.append(f"turn {index + 1}: execution failed")
        if not str(turn.get("answer", "")).strip():
            failures.append(f"turn {index + 1}: answer is empty")
        required_fields = set(required_by_turn[index]) if index < len(required_by_turn) else set()
        missing_fields = required_fields - _pipeline_fields(turn.get("pipeline", []))
        if missing_fields:
            failures.append(
                f"turn {index + 1}: pipeline omitted {sorted(missing_fields)}"
            )

    final_answer = _turns(run)[-1].get("answer", "").lower() if _turns(run) else ""
    missing_terms = [
        term for term in expectations.get("expected_answer_terms", [])
        if term.lower() not in final_answer
    ]
    if missing_terms:
        failures.append(f"final answer omitted {missing_terms}")

    return _feedback(
        "analytical_correctness",
        not failures,
        "; ".join(failures) or "Required business fields and answer checks passed.",
    )


def presentation_correctness(run: Any, example: Any) -> dict[str, object]:
    """Ensure chart requests use the requested JSON payload without duplicate markup."""
    if error := _run_error(run):
        return _feedback(
            "presentation_correctness",
            False,
            f"Target function failed: {error}",
        )

    expected_visualization = _reference_outputs(example).get("expected_visualization")
    turns = _turns(run)
    if not turns:
        return _feedback("presentation_correctness", False, "No turn output was produced.")

    final_turn = turns[-1]
    visualization = final_turn.get("visualization")
    visualization_type = (
        visualization.get("type") if isinstance(visualization, dict) else None
    )
    answer = str(final_turn.get("answer", "")).lower()
    has_duplicate_markup = "```" in answer or "mermaid" in answer

    if expected_visualization == "none":
        passed = visualization is None and not has_duplicate_markup
    elif expected_visualization:
        passed = visualization_type == expected_visualization and not has_duplicate_markup
    else:
        passed = not has_duplicate_markup

    return _feedback(
        "presentation_correctness",
        passed,
        (
            f"expected visualization={expected_visualization}; "
            f"actual visualization={visualization_type}; duplicate markup={has_duplicate_markup}"
        ),
    )


def conversation_context(run: Any, example: Any) -> dict[str, object]:
    """Check that follow-ups reuse or refresh data exactly as their intent requires."""
    if error := _run_error(run):
        return _feedback(
            "conversation_context",
            False,
            f"Target function failed: {error}",
        )

    expected_executions = _reference_outputs(example).get("expected_query_executions")
    turns = _turns(run)
    actual_executions = sum(
        turn.get("route_category") == "analytical" and turn.get("is_valid", False)
        for turn in turns
    )
    passed = actual_executions == expected_executions
    return _feedback(
        "conversation_context",
        passed,
        f"expected query executions={expected_executions}; actual={actual_executions}",
    )


EVALUATORS = (
    route_accuracy,
    mongodb_query_validity,
    analytical_correctness,
    presentation_correctness,
    conversation_context,
)
