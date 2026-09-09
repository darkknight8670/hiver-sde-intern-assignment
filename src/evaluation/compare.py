import json
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GOLDEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "golden"
    / "golden_set.jsonl"
)

TRIVIAL_FILE = (
    PROJECT_ROOT
    / "results"
    / "baselines"
    / "trivial_predictions.jsonl"
)

SIMPLE_FILE = (
    PROJECT_ROOT
    / "results"
    / "baselines"
    / "simple_predictions.jsonl"
)

AGENT_FILE = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
    / "agent_predictions.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
    / "comparison.json"
)


def load_jsonl(path):
    records = []

    if not path.exists():
        return records

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def index_by_id(records):
    return {
        record["example_id"]: record
        for record in records
        if "example_id" in record
    }


def build_evaluation_records(golden, predictions):
    """
    Join predictions with the golden set using example_id.

    This is necessary because the baseline prediction files
    contain predictions but do not contain gold labels.
    """

    gold_by_id = index_by_id(golden)
    prediction_by_id = index_by_id(predictions)

    records = []

    for example_id, prediction in prediction_by_id.items():

        if prediction.get("status") == "error":
            continue

        if example_id not in gold_by_id:
            continue

        gold = gold_by_id[example_id]

        records.append({
            "example_id": example_id,

            "gold_intent": gold["gold_intent"],
            "predicted_intent": prediction["predicted_intent"],

            "gold_routing": gold["gold_routing"],
            "predicted_routing": prediction["predicted_routing"],
        })

    return records


def calculate_metrics(records):

    if not records:
        return None

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

        "intent_accuracy": accuracy_score(
            gold_intents,
            predicted_intents
        ),

        "intent_macro_f1": f1_score(
            gold_intents,
            predicted_intents,
            average="macro",
            zero_division=0
        ),

        "intent_weighted_f1": f1_score(
            gold_intents,
            predicted_intents,
            average="weighted",
            zero_division=0
        ),

        "routing_accuracy": accuracy_score(
            gold_routing,
            predicted_routing
        ),

        "routing_macro_f1": f1_score(
            gold_routing,
            predicted_routing,
            average="macro",
            zero_division=0
        ),

        "routing_weighted_f1": f1_score(
            gold_routing,
            predicted_routing,
            average="weighted",
            zero_division=0
        ),
    }


def print_row(name, metrics):

    if metrics is None:
        print(f"{name:<18} No data")
        return

    print(
        f"{name:<18}"
        f"{metrics['n']:>6}"
        f"{metrics['intent_accuracy'] * 100:>13.2f}%"
        f"{metrics['intent_macro_f1'] * 100:>13.2f}%"
        f"{metrics['routing_accuracy'] * 100:>14.2f}%"
        f"{metrics['routing_macro_f1'] * 100:>14.2f}%"
    )


def main():

    print("=" * 82)
    print("Baseline vs Agent Comparison")
    print("=" * 82)

    golden = load_jsonl(GOLDEN_FILE)
    trivial_predictions = load_jsonl(TRIVIAL_FILE)
    simple_predictions = load_jsonl(SIMPLE_FILE)
    agent_predictions = load_jsonl(AGENT_FILE)

    print()
    print(f"Golden examples:       {len(golden)}")
    print(f"Trivial predictions:   {len(trivial_predictions)}")
    print(f"Simple predictions:    {len(simple_predictions)}")
    print(
        "Final agent predictions: "
        f"{sum(1 for r in agent_predictions if r.get('status') == 'success')}"
    )

    trivial_records = build_evaluation_records(
        golden,
        trivial_predictions
    )

    simple_records = build_evaluation_records(
        golden,
        simple_predictions
    )

    agent_records = build_evaluation_records(
        golden,
        agent_predictions
    )

    judge_predictions = load_jsonl(
        PROJECT_ROOT / "results" / "evaluation" / "llm_judge.jsonl"
    )
    genuine_judge_ids = {
        record["example_id"]
        for record in judge_predictions
        if (
            record.get("status") == "success"
            and not record.get("mock")
            and not record.get("mock_disclaimer")
            and record.get("example_id")
        )
    }
    results = {
        "trivial": calculate_metrics(trivial_records),
        "simple": calculate_metrics(simple_records),
        "groq_agent": calculate_metrics(agent_records),
        "coverage": {
            "golden_n": len(golden),
            "trivial_n": len(trivial_records),
            "simple_n": len(simple_records),
            "final_agent_n": len(agent_records),
            "genuine_judge_n": len(genuine_judge_ids),
        },
    }

    print()
    print(
        f"{'System':<18}"
        f"{'N':>6}"
        f"{'Intent Acc':>14}"
        f"{'Intent F1':>14}"
        f"{'Routing Acc':>15}"
        f"{'Routing F1':>15}"
    )

    print("-" * 82)

    print_row("trivial", results["trivial"])
    print_row("simple", results["simple"])
    print_row("groq_agent", results["groq_agent"])

    print()
    print("Evaluation notes:")
    print(
        "- Gold labels come from the golden set."
    )
    print(
        "- Baseline predictions are joined using example_id."
    )
    print(
        "- Failed API records are excluded."
    )
    print(
        f"- Final-agent evaluation sample size: {len(agent_records)}"
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()