import json
from collections import Counter
from pathlib import Path


GOLDEN_PATH = Path("data/golden/golden_set.jsonl")
OUTPUT_PATH = Path("results/baselines/trivial_predictions.jsonl")


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    golden = load_jsonl(GOLDEN_PATH)

    if not golden:
        raise RuntimeError("Golden set is empty.")

    # ---------------------------------------------------------
    # 1. Find majority intent from the golden set
    # ---------------------------------------------------------
    intent_counts = Counter(
        item["gold_intent"]
        for item in golden
        if item.get("gold_intent")
    )

    if not intent_counts:
        raise RuntimeError("No gold intents found.")

    majority_intent, majority_count = intent_counts.most_common(1)[0]

    # ---------------------------------------------------------
    # 2. Trivial routing baseline
    # ---------------------------------------------------------
    # Deliberately conservative:
    # send every request to a human.
    majority_routing = "human_escalation"

    # ---------------------------------------------------------
    # 3. Trivial response baseline
    # ---------------------------------------------------------
    # Use the most common historical AmazonHelp response
    # appearing in the golden set.
    response_counts = Counter(
        item["historical_response"]
        for item in golden
        if item.get("historical_response")
    )

    default_response, response_count = response_counts.most_common(1)[0]

    # ---------------------------------------------------------
    # 4. Generate predictions
    # ---------------------------------------------------------
    predictions = []

    for item in golden:
        predictions.append({
            "example_id": item["example_id"],
            "conversation_id": item["conversation_id"],
            "customer_message": item["customer_message"],
            "predicted_intent": majority_intent,
            "predicted_routing": majority_routing,
            "predicted_response": default_response,
        })

    # ---------------------------------------------------------
    # 5. Save predictions
    # ---------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for prediction in predictions:
            f.write(json.dumps(prediction, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------
    # 6. Print summary
    # ---------------------------------------------------------
    print("=" * 70)
    print("TRIVIAL BASELINE")
    print("=" * 70)

    print(f"Golden examples : {len(golden):,}")

    print("\nIntent distribution:")
    for intent, count in intent_counts.most_common():
        percentage = 100 * count / sum(intent_counts.values())
        print(f"  {intent:<25} {count:>4} ({percentage:5.1f}%)")

    print("\nMajority intent:")
    print(f"  {majority_intent}")
    print(f"  Count: {majority_count}")

    print("\nRouting:")
    print(f"  {majority_routing}")

    print("\nDefault response:")
    print(f"  {default_response}")

    print(f"\nSaved predictions:")
    print(f"  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()