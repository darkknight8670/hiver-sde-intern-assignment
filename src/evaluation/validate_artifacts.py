"""Validate the offline evaluation artifacts before reporting metrics."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_FILE = PROJECT_ROOT / "data/golden/golden_set.jsonl"
AGENT_FILE = PROJECT_ROOT / "results/evaluation/agent_predictions.jsonl"
EVALUATION_VERSION = "answer-leakage-fixed-v2"


def load_jsonl(path):
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def validate_unique_ids(records, name):
    ids = [record.get("example_id") for record in records]
    if None in ids or len(ids) != len(set(ids)):
        raise RuntimeError(f"{name} contains missing or duplicate example_id values")


def validate_golden(records):
    validate_unique_ids(records, "Golden set")

    contaminated = []
    for record in records:
        historical = record.get("historical_response", "")
        context_text = " ".join(
            turn.get("text", "")
            for turn in record.get("context", [])
            if isinstance(turn, dict)
        )
        if historical and historical in context_text:
            contaminated.append(record["example_id"])

    if contaminated:
        raise RuntimeError(
            "Golden context contains the target historical response for: "
            + ", ".join(contaminated[:10])
        )


def validate_predictions(records, golden_ids):
    successful = [record for record in records if record.get("status") == "success"]
    validate_unique_ids(successful, "Successful agent predictions")

    unknown = {record["example_id"] for record in successful} - golden_ids
    if unknown:
        raise RuntimeError(f"Predictions contain unknown example IDs: {sorted(unknown)}")

    missing_metadata = [
        record["example_id"]
        for record in successful
        if (
            not record.get("provider")
            or not record.get("model")
            or record.get("evaluation_version") != EVALUATION_VERSION
        )
    ]
    if missing_metadata:
        raise RuntimeError(
            "Successful predictions are legacy or missing provider/model "
            "metadata; regenerate them with run_agent: "
            + ", ".join(missing_metadata[:10])
        )


def main():
    golden = load_jsonl(GOLDEN_FILE)
    predictions = load_jsonl(AGENT_FILE)
    validate_golden(golden)
    validate_predictions(predictions, {record["example_id"] for record in golden})
    print(f"PASS: {len(golden)} golden records and evaluation artifacts are valid")


if __name__ == "__main__":
    main()