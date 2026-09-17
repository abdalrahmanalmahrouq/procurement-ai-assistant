from typing import Any

from app.ai.schema.procurement_schema import (
    ALLOWED_FIELDS,
)


ALLOWED_STAGES = {
    "$match",
    "$group",
    "$sort",
    "$limit",
    "$project",
    "$count",
    "$addFields",
    "$set",
    "$unwind",
    "$facet",
    "$skip",
}


FORBIDDEN_OPERATORS = {
    "$out",
    "$merge",
    "$function",
    "$accumulator",
    "$where",
    "$lookup",
    "$unionWith",
}

ALLOWED_GROUP_ACCUMULATORS = {
    "$sum",
    "$avg",
    "$min",
    "$max",
    "$first",
    "$last",
    "$push",
    "$addToSet",
}


MAX_PIPELINE_STAGES = 15
MAX_RESULT_LIMIT = 100

def find_forbidden_operator(
    value: Any
) -> str | None:

    if isinstance(value, dict):

        for key, nested_value in value.items():

            if key in FORBIDDEN_OPERATORS:
                return key

            found = find_forbidden_operator(
                nested_value
            )

            if found:
                return found

    elif isinstance(value, list):

        for item in value:

            found = find_forbidden_operator(
                item
            )

            if found:
                return found

    return None

def validate_match_fields(
    match_expression: dict[str, Any]
) -> str | None:

    for key, value in match_expression.items():

        # Logical MongoDB operators
        if key in {
            "$and",
            "$or",
            "$nor"
        }:

            if not isinstance(value, list):
                return (
                    f"{key} must contain a list."
                )

            for condition in value:

                if not isinstance(
                    condition,
                    dict
                ):
                    return (
                        f"Invalid condition inside "
                        f"{key}."
                    )

                error = validate_match_fields(
                    condition
                )

                if error:
                    return error

            continue

        # Query operator such as $expr
        if key.startswith("$"):

            if key == "$expr":
                continue

            return (
                f"Unsupported match operator: "
                f"{key}"
            )

        # Normal database field
        if key not in ALLOWED_FIELDS:

            return (
                f"Unknown database field in "
                f"$match: {key}"
            )

    return None

def validate_limit(
    value: Any
) -> str | None:

    if not isinstance(value, int):
        return "$limit must be an integer."

    if value < 1:
        return "$limit must be greater than 0."

    if value > MAX_RESULT_LIMIT:
        return (
            f"$limit cannot exceed "
            f"{MAX_RESULT_LIMIT}."
        )

    return None


def validate_pipeline(
    pipeline: list[dict[str, Any]]
) -> tuple[bool, str | None]:

    # -----------------------------
    # Basic structure
    # -----------------------------

    if not isinstance(pipeline, list):

        return (
            False,
            "Pipeline must be a list."
        )

    if not pipeline:

        return (
            False,
            "Pipeline cannot be empty."
        )

    if len(pipeline) > MAX_PIPELINE_STAGES:

        return (
            False,
            (
                "Pipeline contains too many "
                f"stages. Maximum allowed is "
                f"{MAX_PIPELINE_STAGES}."
            )
        )



    # -----------------------------
    # Dangerous operators anywhere
    # -----------------------------

    forbidden = find_forbidden_operator(
        pipeline
    )

    if forbidden:

        return (
            False,
            (
                "Forbidden MongoDB operator "
                f"detected: {forbidden}"
            )
        )

    # -----------------------------
    # Validate every stage
    # -----------------------------

    for index, stage in enumerate(pipeline):

        if not isinstance(stage, dict):

            return (
                False,
                (
                    f"Pipeline stage {index} "
                    "must be an object."
                )
            )

        if len(stage) != 1:

            return (
                False,
                (
                    f"Pipeline stage {index} "
                    "must contain exactly one "
                    "aggregation operator."
                )
            )

        stage_name = next(iter(stage))

        if stage_name not in ALLOWED_STAGES:

            return (
                False,
                (
                    "Unsupported aggregation "
                    f"stage: {stage_name}"
                )
            )

        stage_value = stage[stage_name]

        # -------------------------
        # $match
        # -------------------------

        if stage_name == "$match":

            if not isinstance(
                stage_value,
                dict
            ):
                return (
                    False,
                    "$match must be an object."
                )

            error = validate_match_fields(
                stage_value
            )

            if error:
                return False, error

        # -------------------------
        # $limit
        # -------------------------

        if stage_name == "$limit":

            error = validate_limit(
                stage_value
            )

            if error:
                return False, error

        if stage_name == "$group":

            error = validate_group(
                stage_value
            )

            if error:
                return False, error

    return True, None

def validate_group(
    group_expression: dict[str, Any]
) -> str | None:

    if not isinstance(
        group_expression,
        dict
    ):
        return "$group must be an object."

    if "_id" not in group_expression:
        return (
            "$group must contain an _id field."
        )

    for field, expression in group_expression.items():

        # _id is MongoDB's grouping key
        if field == "_id":
            continue

        # Every other field must be an accumulator
        if not isinstance(expression, dict):
            return (
                f"$group field '{field}' must "
                "contain an accumulator object."
            )

        if len(expression) != 1:
            return (
                f"$group field '{field}' must "
                "contain exactly one accumulator."
            )

        accumulator = next(
            iter(expression)
        )

        if accumulator not in (
            ALLOWED_GROUP_ACCUMULATORS
        ):
            return (
                f"Unsupported $group accumulator: "
                f"{accumulator}"
            )

    return None