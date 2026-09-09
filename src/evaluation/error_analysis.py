import json
from collections import Counter
from pathlib import Path


GOLDEN_PATH = Path("data/golden/golden_set.jsonl")
PREDICTIONS_PATH = Path(
    "results/evaluation/agent_predictions.jsonl"
)


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():

    golden = load_jsonl(GOLDEN_PATH)
    predictions = [
        prediction
        for prediction in load_jsonl(PREDICTIONS_PATH)
        if prediction.get("status") == "success"
    ]

    golden_by_id = {
        item["example_id"]: item
        for item in golden
    }

    # ---------------------------------------------------------
    # Collect errors
    # ---------------------------------------------------------

    intent_errors = []
    routing_errors = []
    routing_false_negatives = []
    routing_false_positives = []
    low_similarity = []

    confusion = Counter()

    for prediction in predictions:

        example_id = prediction["example_id"]

        if example_id not in golden_by_id:
            continue

        gold = golden_by_id[example_id]

        true_intent = gold["gold_intent"]
        pred_intent = prediction["predicted_intent"]

        true_routing = gold["gold_routing"]
        pred_routing = prediction["predicted_routing"]

        if true_intent != pred_intent:

            intent_errors.append({
                "example_id": example_id,
                "message": gold["customer_message"],
                "true_intent": true_intent,
                "predicted_intent": pred_intent,
            })

            confusion[
                (true_intent, pred_intent)
            ] += 1

        if true_routing != pred_routing:

            error = {
                "example_id": example_id,
                "message": gold["customer_message"],
                "true_routing": true_routing,
                "predicted_routing": pred_routing,
            }

            routing_errors.append(error)

            if (
                true_routing == "human_escalation"
                and pred_routing == "auto_handle"
            ):
                routing_false_negatives.append(error)

            elif (
                true_routing == "auto_handle"
                and pred_routing == "human_escalation"
            ):
                routing_false_positives.append(error)

        similarity = prediction.get(
            "retrieval_similarity"
        )

        if similarity is not None and similarity < 0.15:

            low_similarity.append({
                "example_id": example_id,
                "message": gold["customer_message"],
                "similarity": similarity,
                "true_intent": true_intent,
                "predicted_intent": pred_intent,
            })

    # ---------------------------------------------------------
    # Print summary
    # ---------------------------------------------------------

    print("=" * 70)
    print("FINAL AGENT ERROR ANALYSIS")
    print("=" * 70)

    print(f"\nIntent errors       : {len(intent_errors)}")
    print(f"Routing errors      : {len(routing_errors)}")
    print(f"False negatives     : {len(routing_false_negatives)}")
    print(f"False positives     : {len(routing_false_positives)}")
    print(f"Low similarity      : {len(low_similarity)}")

    # ---------------------------------------------------------
    # Intent confusion pairs
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP INTENT CONFUSIONS")
    print("=" * 70)

    for (true_intent, pred_intent), count in confusion.most_common(15):

        print(
            f"{count:>3}  "
            f"{true_intent:<25} -> {pred_intent}"
        )

    # ---------------------------------------------------------
    # Routing false negatives
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ROUTING FALSE NEGATIVES")
    print("=" * 70)

    for error in routing_false_negatives[:10]:

        print(f"\nID: {error['example_id']}")
        print(f"Customer: {error['message']}")
        print(
            f"Gold: {error['true_routing']} | "
            f"Predicted: {error['predicted_routing']}"
        )

    # ---------------------------------------------------------
    # Routing false positives
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ROUTING FALSE POSITIVES")
    print("=" * 70)

    for error in routing_false_positives[:10]:

        print(f"\nID: {error['example_id']}")
        print(f"Customer: {error['message']}")
        print(
            f"Gold: {error['true_routing']} | "
            f"Predicted: {error['predicted_routing']}"
        )

    # ---------------------------------------------------------
    # Low retrieval similarity
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOW RETRIEVAL SIMILARITY")
    print("=" * 70)

    for error in sorted(
        low_similarity,
        key=lambda x: x["similarity"]
    )[:10]:

        print(f"\nID: {error['example_id']}")
        print(f"Similarity: {error['similarity']:.4f}")
        print(f"Customer: {error['message']}")
        print(
            f"Gold: {error['true_intent']} | "
            f"Predicted: {error['predicted_intent']}"
        )

    # ---------------------------------------------------------
    # Save structured error analysis
    # ---------------------------------------------------------

    output = {
        "intent_errors": intent_errors,
        "routing_errors": routing_errors,
        "routing_false_negatives": routing_false_negatives,
        "routing_false_positives": routing_false_positives,
        "low_similarity": low_similarity,
        "intent_confusion": [
            {
                "true": true_intent,
                "predicted": pred_intent,
                "count": count,
            }
            for (true_intent, pred_intent), count
            in confusion.most_common()
        ],
    }

    output_path = Path(
        "results/evaluation/error_analysis.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\nSaved error analysis to:")
    print(f"  {output_path}")


if __name__ == "__main__":
    main()