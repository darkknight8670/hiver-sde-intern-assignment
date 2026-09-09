import json
from pathlib import Path
from collections import Counter

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
)


GOLDEN_PATH = Path("data/golden/golden_set.jsonl")

PREDICTION_FILES = {
    "trivial": Path("results/baselines/trivial_predictions.jsonl"),
    "simple": Path("results/baselines/simple_predictions.jsonl"),
}


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def evaluate_system(name, prediction_path, golden_by_id):
    predictions = load_jsonl(prediction_path)

    y_true_intent = []
    y_pred_intent = []

    y_true_routing = []
    y_pred_routing = []

    missing = 0

    for prediction in predictions:

        example_id = prediction["example_id"]

        if example_id not in golden_by_id:
            missing += 1
            continue

        gold = golden_by_id[example_id]

        y_true_intent.append(gold["gold_intent"])
        y_pred_intent.append(prediction["predicted_intent"])

        y_true_routing.append(gold["gold_routing"])
        y_pred_routing.append(prediction["predicted_routing"])

    if not y_true_intent:
        raise RuntimeError(
            f"No matching examples found for {name}."
        )

    intent_accuracy = accuracy_score(
        y_true_intent,
        y_pred_intent,
    )

    intent_macro_f1 = f1_score(
        y_true_intent,
        y_pred_intent,
        average="macro",
        zero_division=0,
    )

    intent_weighted_f1 = f1_score(
        y_true_intent,
        y_pred_intent,
        average="weighted",
        zero_division=0,
    )

    routing_accuracy = accuracy_score(
        y_true_routing,
        y_pred_routing,
    )

    routing_macro_f1 = f1_score(
        y_true_routing,
        y_pred_routing,
        average="macro",
        zero_division=0,
    )

    print("\n" + "=" * 70)
    print(f"{name.upper()} BASELINE")
    print("=" * 70)

    print(f"Examples evaluated : {len(y_true_intent)}")
    print(f"Missing examples   : {missing}")

    print("\nIntent metrics")
    print("-" * 70)
    print(f"Accuracy           : {intent_accuracy:.4f}")
    print(f"Macro F1           : {intent_macro_f1:.4f}")
    print(f"Weighted F1        : {intent_weighted_f1:.4f}")

    print("\nRouting metrics")
    print("-" * 70)
    print(f"Accuracy           : {routing_accuracy:.4f}")
    print(f"Macro F1           : {routing_macro_f1:.4f}")

    print("\nIntent classification report")
    print("-" * 70)
    print(
        classification_report(
            y_true_intent,
            y_pred_intent,
            zero_division=0,
        )
    )

    print("\nRouting classification report")
    print("-" * 70)
    print(
        classification_report(
            y_true_routing,
            y_pred_routing,
            zero_division=0,
        )
    )

    return {
        "system": name,
        "examples": len(y_true_intent),
        "intent_accuracy": intent_accuracy,
        "intent_macro_f1": intent_macro_f1,
        "intent_weighted_f1": intent_weighted_f1,
        "routing_accuracy": routing_accuracy,
        "routing_macro_f1": routing_macro_f1,
    }


def main():

    print("=" * 70)
    print("HIVER AGENT EVALUATION")
    print("=" * 70)

    golden = load_jsonl(GOLDEN_PATH)

    golden_by_id = {
        item["example_id"]: item
        for item in golden
    }

    print(f"Golden examples : {len(golden):,}")

    results = []

    for name, prediction_path in PREDICTION_FILES.items():

        if not prediction_path.exists():
            print(
                f"\nWARNING: prediction file not found:"
                f"\n  {prediction_path}"
            )
            continue

        result = evaluate_system(
            name,
            prediction_path,
            golden_by_id,
        )

        results.append(result)

    if not results:
        raise RuntimeError(
            "No prediction files were found."
        )

    # ---------------------------------------------------------
    # Comparison table
    # ---------------------------------------------------------

    print("\n\n" + "=" * 70)
    print("BASELINE COMPARISON")
    print("=" * 70)

    print(
        f"{'System':<15}"
        f"{'Intent Acc':>12}"
        f"{'Intent F1':>12}"
        f"{'Routing Acc':>14}"
        f"{'Routing F1':>14}"
    )

    print("-" * 70)

    for result in results:
        print(
            f"{result['system']:<15}"
            f"{result['intent_accuracy']:>12.4f}"
            f"{result['intent_macro_f1']:>12.4f}"
            f"{result['routing_accuracy']:>14.4f}"
            f"{result['routing_macro_f1']:>14.4f}"
        )

    # ---------------------------------------------------------
    # Save metrics
    # ---------------------------------------------------------

    output_path = Path(
        "results/evaluation/baseline_metrics.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
        )

    print("\nMetrics saved to:")
    print(f"  {output_path}")


if __name__ == "__main__":
    main()