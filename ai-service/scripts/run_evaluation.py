"""Create the baseline LangSmith dataset and run a procurement-agent experiment."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime

import_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if import_path not in sys.path:
    sys.path.insert(0, import_path)

from langsmith import Client
from langsmith.evaluation import evaluate

from app.evaluation.criteria import EVALUATORS
from app.evaluation.dataset import (
    EVALUATION_CASES,
    EVALUATION_DATASET_DESCRIPTION,
    EVALUATION_DATASET_NAME,
)
from app.evaluation.runner import run_evaluation_case


def dataset(client: Client):
    """Create the versioned dataset once; existing examples are never replaced."""
    existing = list(client.list_datasets(dataset_name=EVALUATION_DATASET_NAME))
    if existing:
        dataset_record = existing[0]
    else:
        dataset_record = client.create_dataset(
            dataset_name=EVALUATION_DATASET_NAME,
            description=EVALUATION_DATASET_DESCRIPTION,
        )

    existing_case_ids = {
        example.inputs.get("case_id")
        for example in client.list_examples(dataset_id=dataset_record.id)
        if isinstance(example.inputs, dict)
    }
    for case in EVALUATION_CASES:
        if case.case_id not in existing_case_ids:
            client.create_example(
                inputs=case.inputs(),
                outputs=case.outputs(),
                dataset_id=dataset_record.id,
            )
    return dataset_record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the procurement-agent LangSmith baseline or regression suite.",
    )
    parser.add_argument(
        "--experiment-prefix",
        default="procurement-agent-baseline",
        help="Prefix for the LangSmith experiment (use a regression-specific value after changes).",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=1,
        help="Concurrent cases. Keep 1 for a stable baseline against shared data.",
    )
    args = parser.parse_args()

    if not os.getenv("LANGSMITH_API_KEY"):
        raise SystemExit("LANGSMITH_API_KEY is required to create and run the evaluation.")

    client = Client()
    dataset_record = dataset(client)
    results = evaluate(
        run_evaluation_case,
        data=dataset_record.name,
        evaluators=EVALUATORS,
        experiment_prefix=args.experiment_prefix,
        max_concurrency=args.max_concurrency,
        client=client,
        metadata={
            "dataset": EVALUATION_DATASET_NAME,
            "dataset_version": "v1",
            "baseline": args.experiment_prefix == "procurement-agent-baseline",
            "app_environment": os.getenv("APP_ENV", "development"),
            "run_at": datetime.now(UTC).isoformat(),
        },
    )
    print(f"Evaluation submitted for dataset: {dataset_record.name}")
    print(f"Experiment: {getattr(results, 'experiment_name', args.experiment_prefix)}")


if __name__ == "__main__":
    main()
