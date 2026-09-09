"""
Sample a balanced human-annotation set from the AmazonHelp test split.

Important:
- Heuristic intent detection is ONLY used for sampling coverage.
- Heuristic labels are NOT treated as gold labels.
- The resulting records require human annotation.
"""

import json
import random
import re
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_FILE = PROJECT_ROOT / "data" / "processed" / "splits" / "test.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "data" / "golden" / "golden_set.jsonl"

SEED = 42
TARGET_SIZE = 200


# ---------------------------------------------------------------------
# Sampling keywords
#
# These are deliberately broad. They are NOT the final classifier.
# Their only purpose is to find examples covering different topics.
# ---------------------------------------------------------------------

KEYWORDS = {
    "delivery_issue": [
        "delivery",
        "delivered",
        "delivery date",
        "late",
        "delayed",
        "delay",
        "package",
        "parcel",
        "shipment",
        "shipping",
        "courier",
        "carrier",
        "not arrived",
        "haven't received",
        "have not received",
        "where is my package",
    ],

    "order_issue": [
        "order",
        "cancel order",
        "cancel my order",
        "change my order",
        "order status",
        "order number",
        "preorder",
        "pre-order",
        "ordering",
    ],

    "return_refund": [
        "return",
        "refund",
        "refunded",
        "refunds",
        "money back",
        "exchange",
        "return item",
        "returning",
    ],

    "payment_issue": [
        "payment",
        "paid",
        "charge",
        "charged",
        "charged twice",
        "double charge",
        "credit card",
        "debit card",
        "cash on delivery",
        "cod",
        "amazon pay",
        "billing",
    ],

    "account_access": [
        "account",
        "login",
        "log in",
        "sign in",
        "password",
        "otp",
        "verification code",
        "locked",
        "locked out",
        "on hold",
        "security",
        "can't access",
        "cannot access",
    ],

    "product_issue": [
        "product",
        "item",
        "broken",
        "damaged",
        "defective",
        "faulty",
        "wrong item",
        "wrong product",
        "missing part",
        "missing parts",
        "not working",
        "doesn't work",
        "doesnt work",
    ],

    "prime_video": [
        "prime video",
        "primevideo",
        "video",
        "streaming",
        "stream",
        "buffering",
        "episode",
        "movie",
        "watch",
        "playback",
    ],

    "seller_marketplace": [
        "seller",
        "third party",
        "third-party",
        "marketplace",
        "a-to-z",
        "a to z",
        "seller support",
        "seller warranty",
    ],

    "promotion_offer": [
        "promotion",
        "promotional",
        "discount",
        "deal",
        "deals",
        "coupon",
        "voucher",
        "cashback",
        "offer",
        "promo",
    ],

    "prime_membership": [
        "prime membership",
        "prime subscription",
        "prime member",
        "membership",
        "subscription",
        "cancel prime",
        "prime benefits",
        "prime benefit",
    ],

    "customer_service": [
        "customer service",
        "support",
        "agent",
        "representative",
        "representative",
        "contacted support",
        "contact support",
        "called support",
        "nobody helped",
        "no one helped",
        "escalate",
        "escalation",
        "complaint",
        "unresolved",
    ],
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def normalize_text(text):
    """Normalize text for keyword matching."""
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_turns(episode):
    """
    Support the episode format produced by src/data/conversations.py.
    """
    turns = episode.get("turns", [])

    if not isinstance(turns, list):
        return []

    return turns


def get_customer_turns(episode):
    """Return customer turns from a reconstructed episode."""

    turns = get_turns(episode)

    return [
        turn
        for turn in turns
        if turn.get("speaker") == "customer"
    ]


def get_first_customer_turn(episode):
    """Return the first customer message in the episode."""
    customer_turns = get_customer_turns(episode)

    if not customer_turns:
        return None

    return customer_turns[0]


def get_historical_response(episode):
    """
    Return the first AmazonHelp/support response after the first
    customer message.
    """

    turns = get_turns(episode)

    seen_customer = False

    for turn in turns:

        if turn.get("speaker") == "customer":
            seen_customer = True
            continue

        if (
            seen_customer
            and turn.get("speaker") == "support"
        ):
            return turn

    return None


def get_context(episode):
    """
    Return the complete conversation context in chronological order.
    """

    context = []

    for turn in get_turns(episode):

        text = turn.get("text", "")

        if not text:
            continue

        speaker = turn.get("speaker", "unknown")

        context.append({
            "speaker": speaker,
            "text": text,
            "tweet_id": str(
                turn.get("tweet_id", "")
            ),
        })

    return context


def keyword_score(text, keyword_list):
    """Count matching keywords."""
    score = 0

    for keyword in keyword_list:
        if keyword in text:
            score += 1

    return score


def heuristic_intents(text):
    """
    Return intents ranked by simple keyword coverage.

    This is NOT a classifier.
    It exists only to help construct a diverse annotation sample.
    """
    text = normalize_text(text)

    scores = {}

    for intent, keywords in KEYWORDS.items():
        score = keyword_score(text, keywords)

        if score > 0:
            scores[intent] = score

    return sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0])
    )


def sample_candidates(episodes):
    """
    Select examples with broad intent coverage.

    Heuristic categories are used only for sampling diversity.
    They are NOT gold labels.

    Every selected episode must contain at least one customer message.
    """

    rng = random.Random(SEED)

    candidates_by_intent = {
        intent: []
        for intent in KEYWORDS
    }

    uncategorized = []

    # ---------------------------------------------------------------
    # First collect only valid episodes.
    # ---------------------------------------------------------------

    valid_episodes = []

    for episode in episodes:
        customer = get_first_customer_turn(episode)

        if customer is None:
            continue

        text = customer.get("text", "").strip()

        if not text:
            continue

        valid_episodes.append(episode)

        ranked = heuristic_intents(text)

        if ranked:
            # Strongest heuristic bucket is used only for sampling.
            best_intent = ranked[0][0]

            candidates_by_intent[best_intent].append(
                (episode, ranked)
            )
        else:
            uncategorized.append(episode)

    print(
        f"Valid episodes with customer messages: "
        f"{len(valid_episodes):,}"
    )

    # ---------------------------------------------------------------
    # Select approximately equal coverage across the explicit
    # heuristic categories.
    # ---------------------------------------------------------------

    explicit_intents = list(KEYWORDS.keys())

    reserved_other = 20

    remaining_for_explicit = TARGET_SIZE - reserved_other

    per_intent = remaining_for_explicit // len(explicit_intents)

    selected = []
    selected_ids = set()

    sampling_stats = {}

    for intent in explicit_intents:

        pool = candidates_by_intent[intent].copy()

        rng.shuffle(pool)

        chosen = 0

        for episode, ranked in pool:

            episode_id = str(
                episode.get("conversation_id")
                or episode.get("episode_id")
                or episode.get("id")
                or episode.get("tweet_id")
            )

            if episode_id in selected_ids:
                continue

            selected.append(
                (episode, intent, ranked)
            )

            selected_ids.add(episode_id)

            chosen += 1

            if chosen >= per_intent:
                break

        sampling_stats[intent] = chosen

    # ---------------------------------------------------------------
    # Add uncategorized / ambiguous examples.
    # These are useful for testing the "other" class and difficult
    # intent boundaries.
    # ---------------------------------------------------------------

    fallback_pool = []

    # Truly uncategorized examples.
    for episode in uncategorized:
        fallback_pool.append(
            (episode, "other", [])
        )

    # Ambiguous examples:
    # top two heuristic categories have equal scores.
    for intent in explicit_intents:

        for episode, ranked in candidates_by_intent[intent]:

            if len(ranked) < 2:
                continue

            if ranked[0][1] == ranked[1][1]:

                fallback_pool.append(
                    (episode, "ambiguous", ranked)
                )

    rng.shuffle(fallback_pool)

    for episode, bucket, ranked in fallback_pool:

        if len(selected) >= TARGET_SIZE:
            break

        episode_id = str(
            episode.get("conversation_id")
            or episode.get("episode_id")
            or episode.get("id")
            or episode.get("tweet_id")
        )

        if episode_id in selected_ids:
            continue

        selected.append(
            (episode, bucket, ranked)
        )

        selected_ids.add(episode_id)

    sampling_stats["other_or_ambiguous"] = (
        len(selected)
        - sum(sampling_stats.values())
    )

    # ---------------------------------------------------------------
    # Final fallback.
    #
    # IMPORTANT:
    # Only choose from valid episodes containing a customer message.
    # ---------------------------------------------------------------

    if len(selected) < TARGET_SIZE:

        remaining = []

        for episode in valid_episodes:

            episode_id = str(
                episode.get("conversation_id")
                or episode.get("episode_id")
                or episode.get("id")
                or episode.get("tweet_id")
            )

            if episode_id not in selected_ids:
                remaining.append(episode)

        rng.shuffle(remaining)

        for episode in remaining:

            if len(selected) >= TARGET_SIZE:
                break

            selected.append(
                (episode, "unclassified", [])
            )

            episode_id = str(
                episode.get("conversation_id")
                or episode.get("episode_id")
                or episode.get("id")
                or episode.get("tweet_id")
            )

            selected_ids.add(episode_id)

    # ---------------------------------------------------------------
    # Safety assertion.
    # ---------------------------------------------------------------

    assert len(selected) == min(
        TARGET_SIZE,
        len(valid_episodes)
    ), (
        f"Expected {min(TARGET_SIZE, len(valid_episodes))} "
        f"selected examples but got {len(selected)}"
    )

    return selected[:TARGET_SIZE], sampling_stats


def make_annotation_record(episode, sampling_bucket, ranked):
    """Create a human-annotation record."""

    customer = get_first_customer_turn(episode)
    if customer is None:
        raise ValueError(
            "Selected episode does not contain a customer message: "
            f"{episode.get('conversation_id', 'unknown')}"
        )
    historical_response = get_historical_response(episode)

    conversation_id = (
        episode.get("conversation_id")
        or episode.get("episode_id")
        or episode.get("id")
    )

    if conversation_id is None:
        conversation_id = str(customer.get("tweet_id", ""))

    record = {
        "example_id": None,
        "conversation_id": str(conversation_id),

        "customer_message": customer.get("text", "").strip(),

        "context": get_context(episode),

        "historical_response": (
            historical_response.get("text", "").strip()
            if historical_response
            else ""
        ),

        # -----------------------------------------------------------
        # HUMAN ANNOTATION FIELDS
        #
        # These intentionally start empty.
        # -----------------------------------------------------------

        "gold_intent": None,
        "intent_confidence": None,
        "intent_rationale": None,

        "gold_routing": None,
        "routing_reason": None,

        # -----------------------------------------------------------
        # Sampling metadata.
        #
        # These are NOT labels and must not be used as gold truth.
        # -----------------------------------------------------------

        "sampling_bucket": sampling_bucket,

        "sampling_hints": [
            intent
            for intent, score in ranked
        ],
    }

    return record


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 70)
    print("AMAZONHELP GOLDEN SET SAMPLER")
    print("=" * 70)

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test split not found:\n{TEST_FILE}"
        )

    print(f"Reading: {TEST_FILE}")

    episodes = []

    with TEST_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:
            line = line.strip()

            if not line:
                continue

            episodes.append(json.loads(line))

    print(f"Loaded episodes: {len(episodes):,}")

    selected, stats = sample_candidates(episodes)

    print(f"Selected examples: {len(selected):,}")

    # ---------------------------------------------------------------
    # Build annotation records
    # ---------------------------------------------------------------

    records = []

    for index, (episode, bucket, ranked) in enumerate(
        selected,
        start=1
    ):
        record = make_annotation_record(
            episode,
            bucket,
            ranked
        )

        record["example_id"] = f"gold_{index:04d}"

        records.append(record)

    # ---------------------------------------------------------------
    # Write JSONL
    # ---------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    print()
    print("Sampling coverage:")
    print("-" * 50)

    for intent, count in stats.items():
        print(f"{intent:25s}: {count:4d}")

    print()
    print(f"Saved: {OUTPUT_FILE}")

    print()
    print("IMPORTANT:")
    print("The sampling hints are NOT gold labels.")
    print("Human annotation is required before evaluation.")


if __name__ == "__main__":
    main()