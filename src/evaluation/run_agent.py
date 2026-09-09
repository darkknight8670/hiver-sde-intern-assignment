import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AGENT_DIR = PROJECT_ROOT / "src" / "agent"
sys.path.insert(0, str(AGENT_DIR))

from agent import SupportAgent


GOLDEN_FILE = PROJECT_ROOT / "data" / "golden" / "golden_set.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "results" / "evaluation" / "agent_predictions.jsonl"


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


def load_successful_predictions(path):
    """
    Only successful predictions count as completed.

    Error records are deliberately ignored so they can be retried
    on the next run.
    """

    predictions = {}

    if not path.exists():
        return predictions

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            if (
                record.get("status") == "success"
                and record.get("example_id")
            ):
                predictions[record["example_id"]] = record

    return predictions


def append_prediction(path, prediction):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                prediction,
                ensure_ascii=False
            ) + "\n"
        )


def main():

    print("=" * 60)
    print("AmazonHelp Agent Evaluation")
    print("=" * 60)

    golden = load_jsonl(GOLDEN_FILE)

    print(f"Golden examples: {len(golden)}")

    successful = load_successful_predictions(OUTPUT_FILE)

    print(f"Already successful: {len(successful)}")

    remaining = [
        example
        for example in golden
        if example["example_id"] not in successful
    ]

    print(f"Remaining to evaluate: {len(remaining)}")

    if not remaining:
        print("\nAll examples already have successful predictions.")
        return

    agent = SupportAgent()

    total = len(golden)

    success_count = len(successful)
    failure_count = 0

    for index, example in enumerate(remaining, start=1):

        example_id = example["example_id"]

        print()
        print("-" * 60)
        print(
            f"[{success_count + failure_count + 1}/{total}] "
            f"{example_id}"
        )

        try:

            result = agent.predict(
                customer_message=example["customer_message"],
                context=example.get("context", [])
            )

            prediction = {
                "example_id": example_id,
                "conversation_id": example["conversation_id"],
                "customer_message": example["customer_message"],
                "gold_intent": example["gold_intent"],
                "gold_routing": example["gold_routing"],
                "predicted_intent": result["intent"],
                "predicted_routing": result["routing"],
                "routing_reason": result["routing_reason"],
                "response": result["response"],
                "retrieved_examples": result["retrieved_examples"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success",
            }

            append_prediction(
                OUTPUT_FILE,
                prediction
            )

            successful[example_id] = prediction
            success_count += 1

            print(f"Intent:   {prediction['predicted_intent']}")
            print(f"Routing:  {prediction['predicted_routing']}")
            print(
                f"Response: "
                f"{prediction['response'][:150]}"
            )

        except Exception as e:

            failure_count += 1

            print(f"ERROR: {e}")

            # IMPORTANT:
            # We do NOT write failures to the prediction file.
            #
            # This means the example will be retried on the next run.

            if "429" in str(e):

                print(
                    "Gemini quota/rate limit detected. "
                    "Stopping this run."
                )

                break

            print(
                "Skipping this example. "
                "It will be retried on the next run."
            )

    print()
    print("=" * 60)
    print("Evaluation run finished")
    print("=" * 60)

    print(f"Successful predictions: {success_count}")
    print(f"Failures this run:      {failure_count}")
    print(f"Remaining:              {len(golden) - success_count}")

    print()
    print(f"Results saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()