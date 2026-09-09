import json
from pathlib import Path


AGENT_FILE = Path("results/evaluation/agent_predictions.jsonl")
OUTPUT_FILE = Path("data/golden/human_review.jsonl")


def load_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main():
    predictions = load_jsonl(AGENT_FILE)

    successful = [
        record
        for record in predictions
        if record.get("status") == "success"
    ]

    print(f"Successful agent predictions: {len(successful)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        for record in successful:

            review = {
                "example_id": record["example_id"],
                "customer_message": record["customer_message"],
                "agent_intent": record["predicted_intent"],
                "agent_routing": record["predicted_routing"],
                "agent_response": record["response"],
                "retrieved_examples": record.get(
                    "retrieved_examples", []
                ),

                "human_acceptable": None,
                "human_grounded": None,
                "human_helpful": None,
                "human_correct": None,
                "human_hallucination": None,
                "human_reason": ""
            }

            f.write(
                json.dumps(
                    review,
                    ensure_ascii=False
                ) + "\n"
            )

    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()