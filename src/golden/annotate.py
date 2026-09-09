import json
from pathlib import Path

INPUT_FILE = Path("data/golden/golden_set.jsonl")

INTENTS = {
    1: "delivery_issue",
    2: "order_issue",
    3: "return_refund",
    4: "payment_issue",
    5: "account_access",
    6: "product_issue",
    7: "prime_video",
    8: "seller_marketplace",
    9: "promotion_offer",
    10: "prime_membership",
    11: "customer_service",
    12: "other",
}


def load_examples():
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def save_examples(examples):
    with INPUT_FILE.open("w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")


def show_example(example, index, total):
    print("\n" + "=" * 80)
    print(f"Example {index}/{total} | {example['example_id']}")
    print("=" * 80)

    print("\nCUSTOMER MESSAGE:")
    print(example["customer_message"])

    print("\nCONTEXT:")
    context = example.get("context", [])

    for turn in context:
        speaker = turn.get("speaker", "unknown").upper()
        text = turn.get("text", "")
        print(f"{speaker}: {text}")

    print("\nHISTORICAL RESPONSE:")
    print(example.get("historical_response", ""))

    print("\nSAMPLING BUCKET:")
    print(example.get("sampling_bucket"))

    print("\nSAMPLING HINTS:")
    print(example.get("sampling_hints"))


def get_intent():
    print("\nINTENTS:")
    for number, name in INTENTS.items():
        print(f"{number}. {name}")

    while True:
        value = input(
            "\nIntent [1-12] "
            "(Enter = use suggested/previous, q = quit): "
        ).strip().lower()

        if value == "q":
            return None

        if value == "":
            return ""

        try:
            number = int(value)
            if number in INTENTS:
                return INTENTS[number]
        except ValueError:
            pass

        print("Please enter a number from 1 to 12.")


def get_confidence():
    print("\nConfidence:")
    print("h = high")
    print("m = medium")
    print("l = low")

    while True:
        value = input("Confidence [h/m/l, Enter = high]: ").strip().lower()

        if value == "":
            return "high"

        if value == "h":
            return "high"
        if value == "m":
            return "medium"
        if value == "l":
            return "low"

        print("Enter h, m, or l.")


def get_routing():
    print("\nRouting:")
    print("1. auto_handle")
    print("2. human_escalation")

    while True:
        value = input("Routing [1/2, Enter = auto_handle]: ").strip().lower()

        if value == "":
            return "auto_handle"

        if value == "1":
            return "auto_handle"
        if value == "2":
            return "human_escalation"

        print("Enter 1 or 2.")


def get_text(prompt, default=""):
    if default:
        value = input(f"{prompt} [Enter = keep current]: ").strip()
        return value if value else default

    return input(f"{prompt}: ").strip()


def is_annotated(example):
    return (
        example.get("gold_intent") is not None
        and example.get("gold_routing") is not None
    )


def main():
    examples = load_examples()

    total = len(examples)

    print(f"Loaded {total} golden examples.")

    for index, example in enumerate(examples, start=1):

        if is_annotated(example):
            continue

        show_example(example, index, total)

        # ---------------------------------------------------------
        # FAST MODE
        # ---------------------------------------------------------
        print("\nFAST ANNOTATION")
        print("You only need to enter the intent and routing.")
        print("Confidence defaults to HIGH.")
        print("Rationale can be very short.")
        print("Type q at intent to quit.\n")

        intent = get_intent()

        if intent is None:
            save_examples(examples)
            print("\nSaved progress. Exiting.")
            return

        # Intent is required
        while intent == "":
            print("Intent is required.")
            intent = get_intent()

            if intent is None:
                save_examples(examples)
                print("\nSaved progress. Exiting.")
                return

        confidence = get_confidence()

        rationale = get_text(
            "Intent rationale",
            f"The customer is asking about {intent.replace('_', ' ')}."
        )

        routing = get_routing()

        if routing == "auto_handle":
            default_reason = (
                "This is a common support issue that can usually be "
                "handled with standard guidance."
            )
        else:
            default_reason = (
                "This issue requires case-specific investigation or resolution."
            )

        routing_reason = get_text(
            "Routing reason",
            default_reason
        )

        example["gold_intent"] = intent
        example["intent_confidence"] = confidence
        example["intent_rationale"] = rationale
        example["gold_routing"] = routing
        example["routing_reason"] = routing_reason

        save_examples(examples)

        print("\n✓ Saved.")

    print("\n" + "=" * 80)
    print("ALL EXAMPLES ANNOTATED")
    print("=" * 80)


if __name__ == "__main__":
    main()