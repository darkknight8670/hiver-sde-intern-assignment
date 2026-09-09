import json
from pathlib import Path

FILE = Path("data/golden/human_review.jsonl")


def load_jsonl():
    records = []

    with open(FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main():
    records = load_jsonl()

    print("=" * 80)
    print("HUMAN REVIEW")
    print("=" * 80)
    print(f"Examples to review: {len(records)}")
    print()

    for i, record in enumerate(records, start=1):

        print("=" * 80)
        print(f"EXAMPLE {i}/{len(records)}")
        print(f"ID: {record['example_id']}")
        print("=" * 80)

        print("\nCUSTOMER:")
        print(record["customer_message"])

        print("\nAGENT INTENT:")
        print(record["agent_intent"])

        print("\nAGENT ROUTING:")
        print(record["agent_routing"])

        print("\nAGENT RESPONSE:")
        print(record["agent_response"])

        print("\nHISTORICAL EXAMPLES:")

        for j, example in enumerate(
            record.get("retrieved_examples", [])[:3],
            start=1
        ):
            print(f"\n  [{j}] Similarity: {example.get('similarity', 0):.4f}")
            print(f"  Customer: {example.get('customer_message', '')}")
            print(f"  Support:  {example.get('historical_response', '')}")

        print()
        print("-" * 80)
        print("Review this response:")
        print()
        print("Acceptable?       [y/n]")
        print("Grounded?         [y/n]")
        print("Helpful?          [y/n]")
        print("Correct?          [y/n]")
        print("Hallucination?    [y/n]")
        print()
        print("Reason:")
        print("-" * 80)

        input("\nPress ENTER when reviewed...")


if __name__ == "__main__":
    main()