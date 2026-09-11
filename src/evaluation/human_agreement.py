"""Compute agreement between LLM-judge and human ratings.

Input JSONL records must contain matching ``example_id`` values and an
integer ``overall`` score from both ``llm_overall`` and ``human_overall``.
This command intentionally refuses to manufacture human ratings.
"""

import json
import sys
from pathlib import Path

from sklearn.metrics import cohen_kappa_score, mean_absolute_error


def load_records(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.evaluation.human_agreement ratings.jsonl")

    records = load_records(sys.argv[1])
    if not records:
        raise RuntimeError("No human ratings supplied")

    llm = [record["llm_overall"] for record in records]
    human = [record["human_overall"] for record in records]

    if len(llm) != len(human):
        raise RuntimeError("LLM and human rating counts differ")

    missing = [
        record["example_id"]
        for record in records
        if record.get("human_overall") is None
    ]
    if missing:
        raise RuntimeError(
            "Fill human_overall with a real 1-5 rating for: "
            + ", ".join(missing)
        )

    print(f"Examples: {len(records)}")
    print(f"Exact agreement: {sum(a == b for a, b in zip(llm, human)) / len(records):.4f}")
    print(f"Adjacent agreement: {sum(abs(a - b) <= 1 for a, b in zip(llm, human)) / len(records):.4f}")
    print(f"Cohen kappa: {cohen_kappa_score(human, llm, weights='quadratic'):.4f}")
    print(f"Mean absolute error: {mean_absolute_error(human, llm):.4f}")


if __name__ == "__main__":
    main()