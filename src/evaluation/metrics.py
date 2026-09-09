import json
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    f1_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
    / "agent_predictions.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
    / "evaluation_summary.json"
)


def load_successful_predictions(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            # IMPORTANT:
            # Only actual model predictions are evaluated.
            if record.get("status") == "success":
                records.append(record)

    return records


def calculate_metrics(records):

    if not records:
        raise RuntimeError("No successful predictions found.")

    gold_intents = [
        r["gold_intent"]
        for r in records
    ]

    predicted_intents = [
        r["predicted_intent"]
        for r in records
    ]

    gold_routing = [
        r["gold_routing"]
        for r in records
    ]

    predicted_routing = [
        r["predicted_routing"]
        for r in records
    ]

    return {
        "n": len(records),

        "intent": {
            "accuracy": accuracy_score(
                gold_intents,
                predicted_intents
            ),
            "macro_f1": f1_score(
                gold_intents,
                predicted_intents,
                average="macro",
                zero_division=0
            ),
            "weighted_f1": f1_score(
                gold_intents,
                predicted_intents,
                average="weighted",
                zero_division=0
            ),
        },

        "routing": {
            "accuracy": accuracy_score(
                gold_routing,
                predicted_routing
            ),
            "macro_f1": f1_score(
                gold_routing,
                predicted_routing,
                average="macro",
                zero_division=0
            ),
            "weighted_f1": f1_score(
                gold_routing,
                predicted_routing,
                average="weighted",
                zero_division=0
            ),
        },
    }


def main():

    print("=" * 60)
    print("Agent Evaluation Metrics")
    print("=" * 60)

    records = load_successful_predictions(
        PREDICTIONS_FILE
    )

    print(f"Successful predictions: {len(records)}")

    metrics = calculate_metrics(records)

    print()
    print("Intent")
    print(
        f"  Accuracy:   {metrics['intent']['accuracy']:.4f}"
    )
    print(
        f"  Macro F1:   {metrics['intent']['macro_f1']:.4f}"
    )
    print(
        f"  Weighted F1: {metrics['intent']['weighted_f1']:.4f}"
    )

    print()
    print("Routing")
    print(
        f"  Accuracy:   {metrics['routing']['accuracy']:.4f}"
    )
    print(
        f"  Macro F1:   {metrics['routing']['macro_f1']:.4f}"
    )
    print(
        f"  Weighted F1: {metrics['routing']['weighted_f1']:.4f}"
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metrics,
            f,
            indent=2
        )

    print()
    print(f"Saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()