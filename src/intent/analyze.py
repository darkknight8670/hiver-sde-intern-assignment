import json
import re
import os
from pathlib import Path
from collections import Counter, defaultdict


INPUT_PATH = os.getenv(
    "TRAIN_PATH",
    "data/processed/splits/train.jsonl"
)

OUTPUT_DIR = Path(
    "results/intent_analysis"
)


# ---------------------------------------------------------
# Loading
# ---------------------------------------------------------

def load_episodes(path):
    episodes = []

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            episodes.append(
                json.loads(line)
            )

    return episodes


# ---------------------------------------------------------
# Text utilities
# ---------------------------------------------------------

def normalize(text):
    """
    Lightweight normalization for lexical analysis.
    """

    text = text.lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"@\w+",
        " ",
        text
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


STOPWORDS = {
    "the", "and", "for", "you", "your",
    "this", "that", "with", "have", "has",
    "had", "was", "were", "are", "am",
    "from", "they", "them", "their",
    "there", "here", "just", "not",
    "but", "what", "when", "where",
    "why", "how", "can", "could",
    "would", "should", "will", "been",
    "being", "about", "into", "out",
    "get", "got", "getting", "please",
    "thanks", "thank", "amazon",
    "help", "hi", "hello"
}


def tokenize(text):

    words = normalize(text).split()

    return [
        word
        for word in words
        if (
            len(word) >= 3
            and word not in STOPWORDS
        )
    ]


# ---------------------------------------------------------
# Extract customer -> support pairs
# ---------------------------------------------------------

def extract_pairs(episodes):

    pairs = []

    for episode in episodes:

        turns = episode.get(
            "turns",
            []
        )

        for i in range(
            len(turns) - 1
        ):

            customer = turns[i]

            support = turns[i + 1]

            if (
                customer.get("speaker")
                == "customer"
                and
                support.get("speaker")
                == "support"
            ):

                pairs.append({
                    "episode_id": episode.get(
                        "episode_id"
                    ),
                    "customer": customer.get(
                        "text",
                        ""
                    ),
                    "support": support.get(
                        "text",
                        ""
                    )
                })

    return pairs


# ---------------------------------------------------------
# Keyword analysis
# ---------------------------------------------------------

def top_customer_terms(
    pairs,
    limit=100
):

    counter = Counter()

    for pair in pairs:

        counter.update(
            tokenize(
                pair["customer"]
            )
        )

    return counter.most_common(
        limit
    )


def top_support_terms(
    pairs,
    limit=100
):

    counter = Counter()

    for pair in pairs:

        counter.update(
            tokenize(
                pair["support"]
            )
        )

    return counter.most_common(
        limit
    )


# ---------------------------------------------------------
# Candidate keyword groups
# ---------------------------------------------------------

KEYWORD_GROUPS = {

    "delivery": [
        "delivery",
        "delivered",
        "deliver",
        "shipping",
        "shipment",
        "parcel",
        "package",
        "courier",
        "arrived",
        "arrival",
        "late",
        "delay",
        "delayed"
    ],

    "order": [
        "order",
        "orders",
        "ordered",
        "ordering",
        "cancel",
        "cancelled",
        "canceled"
    ],

    "refund_return": [
        "refund",
        "refunds",
        "return",
        "returns",
        "returned",
        "money",
        "reimburse"
    ],

    "payment": [
        "payment",
        "payments",
        "pay",
        "paid",
        "card",
        "credit",
        "debit",
        "cash",
        "cod",
        "charge",
        "charged"
    ],

    "account": [
        "account",
        "login",
        "log",
        "password",
        "signin",
        "sign",
        "code",
        "access",
        "blocked",
        "blocking",
        "locked"
    ],

    "prime_video": [
        "prime",
        "video",
        "movie",
        "movies",
        "stream",
        "streaming",
        "episode",
        "watch",
        "watching",
        "play",
        "playback"
    ],

    "product": [
        "product",
        "item",
        "defective",
        "defect",
        "broken",
        "damaged",
        "damage",
        "faulty",
        "wrong",
        "missing"
    ],

    "seller": [
        "seller",
        "seller",
        "marketplace",
        "vendor",
        "merchant"
    ],

    "promotion": [
        "offer",
        "offers",
        "deal",
        "deals",
        "discount",
        "discounts",
        "coupon",
        "cashback",
        "promo"
    ],

    "customer_service": [
        "customer",
        "service",
        "support",
        "agent",
        "phone",
        "chat",
        "email",
        "response",
        "respond",
        "waiting",
        "wait"
    ]
}


def keyword_distribution(pairs):

    results = {}

    for group, keywords in KEYWORD_GROUPS.items():

        matching_pairs = []

        for pair in pairs:

            text = normalize(
                pair["customer"]
            )

            if any(
                keyword in text
                for keyword in keywords
            ):

                matching_pairs.append(
                    pair
                )

        results[group] = {
            "count": len(
                matching_pairs
            ),
            "percentage": round(
                len(matching_pairs)
                / len(pairs)
                * 100,
                2
            ),
            "examples": [
                {
                    "customer": p["customer"],
                    "support": p["support"]
                }
                for p in matching_pairs[:10]
            ]
        }

    return results


# ---------------------------------------------------------
# Response patterns
# ---------------------------------------------------------

def support_response_patterns(pairs):

    patterns = {

        "asks_for_more_information": [
            "describe the issue",
            "provide",
            "details",
            "could you",
            "please let us know",
            "let us know",
            "tell us"
        ],

        "redirects_to_customer_service": [
            "customer service",
            "phone or chat",
            "contact us",
            "call us"
        ],

        "asks_customer_to_dm": [
            "dm",
            "direct message",
            "message us"
        ],

        "troubleshooting": [
            "restart",
            "reboot",
            "force stop",
            "try again",
            "troubleshoot"
        ],

        "provides_link": [
            "https://",
            "http://"
        ],

        "apology": [
            "sorry",
            "apolog"
        ]
    }

    results = {}

    for pattern_name, phrases in patterns.items():

        matching = []

        for pair in pairs:

            support = normalize(
                pair["support"]
            )

            if any(
                phrase in support
                for phrase in phrases
            ):

                matching.append(pair)

        results[pattern_name] = {
            "count": len(matching),
            "percentage": round(
                len(matching)
                / len(pairs)
                * 100,
                2
            ),
            "examples": [
                {
                    "customer": p["customer"],
                    "support": p["support"]
                }
                for p in matching[:10]
            ]
        }

    return results


# ---------------------------------------------------------
# Save report
# ---------------------------------------------------------

def save_report(
    pairs,
    customer_terms,
    support_terms,
    keyword_results,
    response_results
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    json_path = (
        OUTPUT_DIR
        / "intent_analysis.json"
    )

    data = {
        "num_customer_support_pairs": len(
            pairs
        ),
        "top_customer_terms": customer_terms,
        "top_support_terms": support_terms,
        "keyword_groups": keyword_results,
        "support_response_patterns": response_results
    }

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    md_path = (
        OUTPUT_DIR
        / "intent_analysis.md"
    )

    with open(
        md_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "# AmazonHelp Intent Analysis\n\n"
        )

        f.write(
            f"Customer → support pairs: "
            f"**{len(pairs):,}**\n\n"
        )

        # -------------------------------------------------
        # Customer terms
        # -------------------------------------------------

        f.write(
            "## Top Customer Terms\n\n"
        )

        for term, count in customer_terms:

            f.write(
                f"- `{term}` — {count:,}\n"
            )

        # -------------------------------------------------
        # Support terms
        # -------------------------------------------------

        f.write(
            "\n## Top Support Terms\n\n"
        )

        for term, count in support_terms:

            f.write(
                f"- `{term}` — {count:,}\n"
            )

        # -------------------------------------------------
        # Keyword groups
        # -------------------------------------------------

        f.write(
            "\n## Candidate Support Themes\n\n"
        )

        for name, result in keyword_results.items():

            f.write(
                f"### {name}\n\n"
            )

            f.write(
                f"Matches: "
                f"**{result['count']:,}** "
                f"({result['percentage']}%)\n\n"
            )

            f.write(
                "Examples:\n\n"
            )

            for example in result[
                "examples"
            ]:

                f.write(
                    f"**Customer:** "
                    f"{example['customer']}\n\n"
                )

                f.write(
                    f"**AmazonHelp:** "
                    f"{example['support']}\n\n"
                )

        # -------------------------------------------------
        # Response patterns
        # -------------------------------------------------

        f.write(
            "\n## AmazonHelp Response Patterns\n\n"
        )

        for name, result in response_results.items():

            f.write(
                f"### {name}\n\n"
            )

            f.write(
                f"Matches: "
                f"**{result['count']:,}** "
                f"({result['percentage']}%)\n\n"
            )

            for example in result[
                "examples"
            ][:5]:

                f.write(
                    f"- Customer: "
                    f"{example['customer']}\n"
                )

                f.write(
                    f"  Support: "
                    f"{example['support']}\n\n"
                )

    print(
        f"Saved:\n"
        f"  {json_path}\n"
        f"  {md_path}"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("AMAZONHELP SUPPORT INTENT ANALYSIS")
    print("=" * 60)

    print(
        f"Loading: {INPUT_PATH}"
    )

    episodes = load_episodes(
        INPUT_PATH
    )

    print(
        f"Episodes: {len(episodes):,}"
    )

    pairs = extract_pairs(
        episodes
    )

    print(
        f"Customer → support pairs: "
        f"{len(pairs):,}"
    )

    customer_terms = top_customer_terms(
        pairs
    )

    support_terms = top_support_terms(
        pairs
    )

    keyword_results = keyword_distribution(
        pairs
    )

    response_results = support_response_patterns(
        pairs
    )

    save_report(
        pairs,
        customer_terms,
        support_terms,
        keyword_results,
        response_results
    )

    print()
    print("=" * 60)
    print("CANDIDATE THEME SUMMARY")
    print("=" * 60)

    for name, result in keyword_results.items():

        print(
            f"{name:20s} "
            f"{result['count']:7,} "
            f"({result['percentage']:5.2f}%)"
        )


if __name__ == "__main__":
    main()