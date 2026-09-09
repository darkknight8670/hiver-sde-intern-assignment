import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity


TRAIN_PATH = Path("data/processed/splits/train.jsonl")
GOLDEN_PATH = Path("data/golden/golden_set.jsonl")
OUTPUT_PATH = Path("results/baselines/simple_predictions.jsonl")


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def get_customer_turns(episode):
    return [
        turn.get("text", "")
        for turn in episode.get("turns", [])
        if turn.get("speaker") == "customer"
    ]


def get_support_turns(episode):
    return [
        turn.get("text", "")
        for turn in episode.get("turns", [])
        if turn.get("speaker") == "support"
    ]


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_training_examples(episodes):
    """
    Build customer -> historical support-response examples.

    Each customer turn is paired with the next support response
    in the same episode.
    """

    customer_messages = []
    support_responses = []

    for episode in episodes:
        turns = episode.get("turns", [])

        for i, turn in enumerate(turns):

            if turn.get("speaker") != "customer":
                continue

            customer_text = turn.get("text", "").strip()

            if not customer_text:
                continue

            # Find the next support response.
            support_text = ""

            for next_turn in turns[i + 1:]:
                if next_turn.get("speaker") == "support":
                    support_text = next_turn.get("text", "").strip()
                    break

            if not support_text:
                continue

            customer_messages.append(customer_text)
            support_responses.append(support_text)

    return customer_messages, support_responses


def extract_context(item):
    """
    Combine previous turns from the golden example.

    We deliberately keep this simple.
    """

    context = item.get("context", [])

    if isinstance(context, list):
        return " ".join(
            turn.get("text", "")
            for turn in context
            if isinstance(turn, dict)
        )

    if isinstance(context, str):
        return context

    return ""


def build_routing_prediction(customer_message, context):
    """
    Simple deterministic escalation rules.

    Escalate when the customer:
    - reports hacking/security issues
    - says previous support failed
    - reports repeated contacts
    - reports a missing/misdelivered package
    - explicitly requests escalation/help from a human
    """

    text = normalize_text(
        customer_message + " " + context
    )

    escalation_patterns = [
        r"\bhacked\b",
        r"\bhack\b",
        r"\bstolen\b",
        r"\bsecurity\b",
        r"\bunauthorized\b",
        r"\bnot delivered\b",
        r"\bmissing\b",
        r"\bmisdelivered\b",
        r"\bwrong address\b",
        r"\bnever received\b",
        r"\bpreviously contacted\b",
        r"\balready contacted\b",
        r"\bcontacted support\b",
        r"\bno response\b",
        r"\bno one\b",
        r"\bsupervisor\b",
        r"\bmanager\b",
        r"\bescalat",
        r"\bhuman\b",
    ]

    for pattern in escalation_patterns:
        if re.search(pattern, text):
            return "human_escalation"

    return "auto_handle"


def main():

    print("=" * 70)
    print("SIMPLE BASELINE")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load data
    # ---------------------------------------------------------

    train = load_jsonl(TRAIN_PATH)
    golden = load_jsonl(GOLDEN_PATH)

    print(f"Training episodes : {len(train):,}")
    print(f"Golden examples   : {len(golden):,}")

    # ---------------------------------------------------------
    # 2. Build training data
    # ---------------------------------------------------------

    customer_messages, support_responses = build_training_examples(
        train
    )

    print(
        f"Training customer-response pairs : "
        f"{len(customer_messages):,}"
    )

    # ---------------------------------------------------------
    # 3. Train TF-IDF intent model
    #
    # IMPORTANT:
    # We don't have intent labels in train.jsonl.
    #
    # Therefore the simple baseline cannot train a supervised
    # intent classifier directly from the reconstructed split.
    #
    # Instead, we construct intent prototypes from the golden
    # labels ONLY AFTER creating the retrieval representation.
    #
    # To avoid leaking golden labels into training, this baseline
    # uses nearest-neighbour retrieval over training responses
    # and maps retrieved examples to intent using keyword rules.
    # ---------------------------------------------------------

    # Vectorizer for customer messages.
    vectorizer = TfidfVectorizer(
        preprocessor=normalize_text,
        ngram_range=(1, 2),
        min_df=2,
        max_features=100000,
        sublinear_tf=True,
    )

    train_matrix = vectorizer.fit_transform(
        customer_messages
    )

    print(
        f"TF-IDF vocabulary : "
        f"{len(vectorizer.vocabulary_):,}"
    )

    # ---------------------------------------------------------
    # 4. Retrieve historical response
    # ---------------------------------------------------------

    golden_messages = [
        item["customer_message"]
        for item in golden
    ]

    golden_matrix = vectorizer.transform(
        golden_messages
    )

    similarities = cosine_similarity(
        golden_matrix,
        train_matrix
    )

    # ---------------------------------------------------------
    # 5. Intent inference
    # ---------------------------------------------------------
    #
    # Because train.jsonl has no gold intent labels, use
    # lightweight keyword rules to classify the customer message.
    #
    # This is intentionally simple and interpretable.
    # ---------------------------------------------------------

    INTENT_RULES = {
        "delivery_issue": [
            "delivery",
            "delivered",
            "late",
            "delay",
            "delayed",
            "shipping",
            "shipment",
            "courier",
            "package",
            "parcel",
            "tracking",
            "arrive",
        ],

        "order_issue": [
            "order",
            "cancel order",
            "change order",
            "pre order",
            "pre-order",
        ],

        "return_refund": [
            "refund",
            "return",
            "returned",
            "replacement",
            "money back",
        ],

        "payment_issue": [
            "payment",
            "charged",
            "charge",
            "credit card",
            "debit card",
            "cod",
            "cash on delivery",
            "amazon pay",
        ],

        "account_access": [
            "account",
            "login",
            "log in",
            "password",
            "otp",
            "hacked",
            "hack",
            "locked",
            "security",
        ],

        "product_issue": [
            "broken",
            "damaged",
            "defective",
            "wrong item",
            "wrong product",
            "missing item",
            "product",
            "item",
        ],

        "prime_video": [
            "prime video",
            "fire stick",
            "fire tv",
            "buffering",
            "streaming",
            "movie",
            "video",
        ],

        "seller_marketplace": [
            "seller",
            "third party",
            "third-party",
            "marketplace",
            "a-to-z",
            "a to z",
        ],

        "promotion_offer": [
            "discount",
            "deal",
            "coupon",
            "cashback",
            "cash back",
            "promotion",
            "offer",
        ],

        "prime_membership": [
            "prime membership",
            "prime member",
            "prime trial",
            "prime subscription",
            "join prime",
            "cancel prime",
        ],

        "customer_service": [
            "customer service",
            "support",
            "supervisor",
            "manager",
            "complaint",
            "no response",
            "nobody helped",
        ],
    }

    def predict_intent(text):

        normalized = normalize_text(text)

        scores = {}

        for intent, keywords in INTENT_RULES.items():

            score = 0

            for keyword in keywords:

                keyword_normalized = normalize_text(keyword)

                if keyword_normalized in normalized:
                    score += 1

            scores[intent] = score

        best_intent = max(
            scores,
            key=scores.get
        )

        if scores[best_intent] == 0:
            return "other"

        return best_intent

    # ---------------------------------------------------------
    # 6. Generate predictions
    # ---------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        for i, item in enumerate(golden):

            customer_message = item["customer_message"]

            # Best historical match.
            best_index = similarities[i].argmax()

            historical_response = support_responses[
                best_index
            ]

            predicted_intent = predict_intent(
                customer_message
            )

            context = extract_context(item)

            predicted_routing = build_routing_prediction(
                customer_message,
                context
            )

            prediction = {
                "example_id": item["example_id"],
                "conversation_id": item["conversation_id"],
                "customer_message": customer_message,
                "predicted_intent": predicted_intent,
                "predicted_routing": predicted_routing,
                "predicted_response": historical_response,
                "retrieval_similarity": float(
                    similarities[i].max()
                ),
            }

            f.write(
                json.dumps(
                    prediction,
                    ensure_ascii=False
                ) + "\n"
            )

    # ---------------------------------------------------------
    # 7. Summary
    # ---------------------------------------------------------

    print("\nPredictions generated :", len(golden))

    print(
        "\nAverage retrieval similarity : "
        f"{similarities.max(axis=1).mean():.4f}"
    )

    print(
        "Minimum retrieval similarity : "
        f"{similarities.max(axis=1).min():.4f}"
    )

    print(
        "Maximum retrieval similarity : "
        f"{similarities.max(axis=1).max():.4f}"
    )

    print("\nSaved predictions to:")
    print(f"  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()