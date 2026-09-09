"""
Inspect the sampled AmazonHelp golden set before human annotation.

This script does NOT modify the golden set.
It only reports sampling coverage and shows representative examples.
"""

import json
import statistics
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GOLDEN_FILE = PROJECT_ROOT / "data" / "golden" / "golden_set.jsonl"

SHOW_PER_BUCKET = 3


def load_records():
    records = []

    with GOLDEN_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main():

    print("=" * 75)
    print("AMAZONHELP GOLDEN SET INSPECTION")
    print("=" * 75)

    if not GOLDEN_FILE.exists():
        raise FileNotFoundError(
            f"Golden set not found:\n{GOLDEN_FILE}"
        )

    records = load_records()

    print(f"Golden examples: {len(records):,}")

    if not records:
        print("Golden set is empty.")
        return

    # ---------------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------------

    required_fields = [
        "example_id",
        "conversation_id",
        "customer_message",
        "context",
        "historical_response",
        "gold_intent",
        "intent_confidence",
        "intent_rationale",
        "gold_routing",
        "routing_reason",
        "sampling_bucket",
        "sampling_hints",
    ]

    print()
    print("Field validation")
    print("-" * 75)

    for field in required_fields:

        missing = sum(
            1
            for record in records
            if field not in record
        )

        print(
            f"{field:25s}: "
            f"{'OK' if missing == 0 else f'{missing} missing'}"
        )

    # ---------------------------------------------------------------
    # Sampling buckets
    # ---------------------------------------------------------------

    bucket_counts = Counter(
        record.get("sampling_bucket", "missing")
        for record in records
    )

    print()
    print("Sampling bucket distribution")
    print("-" * 75)

    for bucket, count in bucket_counts.most_common():
        percentage = count / len(records) * 100

        print(
            f"{bucket:25s}: "
            f"{count:4d} "
            f"({percentage:5.1f}%)"
        )

    # ---------------------------------------------------------------
    # Conversation length
    # ---------------------------------------------------------------

    turn_counts = []

    for record in records:
        context = record.get("context", [])

        if isinstance(context, list):
            turn_counts.append(len(context))

    print()
    print("Conversation length")
    print("-" * 75)

    if turn_counts:

        print(
            f"Minimum turns : {min(turn_counts)}"
        )

        print(
            f"Maximum turns : {max(turn_counts)}"
        )

        print(
            f"Average turns : "
            f"{statistics.mean(turn_counts):.2f}"
        )

        print(
            f"Median turns  : "
            f"{statistics.median(turn_counts):.2f}"
        )

        single_turn = sum(
            1
            for count in turn_counts
            if count == 1
        )

        multi_turn = sum(
            1
            for count in turn_counts
            if count > 1
        )

        print(
            f"Single-turn   : "
            f"{single_turn:4d} "
            f"({single_turn / len(turn_counts) * 100:5.1f}%)"
        )

        print(
            f"Multi-turn    : "
            f"{multi_turn:4d} "
            f"({multi_turn / len(turn_counts) * 100:5.1f}%)"
        )

    # ---------------------------------------------------------------
    # Customer message length
    # ---------------------------------------------------------------

    message_lengths = [
        len(record.get("customer_message", ""))
        for record in records
    ]

    print()
    print("Customer message length")
    print("-" * 75)

    print(
        f"Minimum characters : {min(message_lengths)}"
    )

    print(
        f"Maximum characters : {max(message_lengths)}"
    )

    print(
        f"Average characters : "
        f"{statistics.mean(message_lengths):.1f}"
    )

    print(
        f"Median characters  : "
        f"{statistics.median(message_lengths):.1f}"
    )

    # ---------------------------------------------------------------
    # Empty / suspicious records
    # ---------------------------------------------------------------

    empty_messages = [
        record
        for record in records
        if not record.get("customer_message", "").strip()
    ]

    missing_history = [
        record
        for record in records
        if not record.get("historical_response", "").strip()
    ]

    print()
    print("Data quality")
    print("-" * 75)

    print(
        f"Empty customer messages     : "
        f"{len(empty_messages)}"
    )

    print(
        f"Missing historical response : "
        f"{len(missing_history)}"
    )

    # ---------------------------------------------------------------
    # Show representative examples from every bucket
    # ---------------------------------------------------------------

    print()
    print("=" * 75)
    print("REPRESENTATIVE EXAMPLES")
    print("=" * 75)

    grouped = {}

    for record in records:

        bucket = record.get(
            "sampling_bucket",
            "missing"
        )

        grouped.setdefault(
            bucket,
            []
        ).append(record)

    for bucket in sorted(grouped):

        examples = grouped[bucket]

        print()
        print("-" * 75)
        print(
            f"BUCKET: {bucket} "
            f"({len(examples)} examples)"
        )
        print("-" * 75)

        for record in examples[:SHOW_PER_BUCKET]:

            print()
            print(
                f"ID: {record.get('example_id')}"
            )

            print(
                f"Conversation: "
                f"{record.get('conversation_id')}"
            )

            print(
                f"Customer:\n"
                f"  {record.get('customer_message', '')}"
            )

            print(
                f"Historical AmazonHelp:\n"
                f"  {record.get('historical_response', '')}"
            )

            hints = record.get(
                "sampling_hints",
                []
            )

            print(
                f"Sampling hints: "
                f"{', '.join(hints) if hints else 'none'}"
            )

    # ---------------------------------------------------------------
    # Gold labels should still be empty
    # ---------------------------------------------------------------

    annotated_intents = sum(
        1
        for record in records
        if record.get("gold_intent") is not None
    )

    annotated_routing = sum(
        1
        for record in records
        if record.get("gold_routing") is not None
    )

    print()
    print("=" * 75)
    print("ANNOTATION STATUS")
    print("=" * 75)

    print(
        f"Gold intents already filled   : "
        f"{annotated_intents}/{len(records)}"
    )

    print(
        f"Gold routing already filled   : "
        f"{annotated_routing}/{len(records)}"
    )

    if annotated_intents == 0 and annotated_routing == 0:
        print()
        print(
            "STATUS: Ready for human annotation."
        )
    else:
        print()
        print(
            "WARNING: Some gold fields are already populated."
        )


if __name__ == "__main__":
    main()