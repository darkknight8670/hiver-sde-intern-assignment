import json
import random
import os
from pathlib import Path


def load_episodes(path):
    """Load reconstructed episodes from JSONL."""

    episodes = []

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            episodes.append(
                json.loads(line)
            )

    print(
        f"Loaded {len(episodes):,} episodes."
    )

    return episodes


def get_tweet_ids(episode):
    """
    Return all tweet IDs belonging to an episode.
    """

    return {
        str(turn["tweet_id"])
        for turn in episode.get("turns", [])
        if turn.get("tweet_id") is not None
    }


def get_customer_ids(episode):
    """
    Return customer author IDs in an episode.

    Used for reporting only.

    We do NOT use customer IDs as the primary split key
    because TWCS can contain more than one customer account
    participating in the same reply chain.
    """

    return {
        str(turn["author"])
        for turn in episode.get("turns", [])
        if (
            turn.get("speaker") == "customer"
            and turn.get("author")
        )
    }


def get_start_tweet_id(episode):
    """
    Return the canonical starting tweet for an episode.
    """

    return str(
        episode["start_tweet_id"]
    )


def split_episodes(
    episodes,
    train_ratio=0.70,
    validation_ratio=0.15,
    test_ratio=0.15,
    seed=42,
):
    """
    Randomly split complete episodes.

    We never split individual turns.

    The episode is the atomic evaluation unit.
    """

    if abs(
        train_ratio
        + validation_ratio
        + test_ratio
        - 1.0
    ) > 1e-9:

        raise ValueError(
            "Split ratios must sum to 1.0"
        )

    episodes = list(episodes)

    rng = random.Random(seed)

    rng.shuffle(episodes)

    n = len(episodes)

    train_end = int(
        n * train_ratio
    )

    validation_end = (
        train_end
        + int(n * validation_ratio)
    )

    train = episodes[:train_end]

    validation = episodes[
        train_end:validation_end
    ]

    test = episodes[
        validation_end:
    ]

    return train, validation, test


def verify_tweet_overlap(
    train,
    validation,
    test,
):
    """
    Verify that no tweet appears in more than one split.

    This is the primary leakage check.
    """

    train_tweets = set()

    validation_tweets = set()

    test_tweets = set()

    for episode in train:
        train_tweets.update(
            get_tweet_ids(episode)
        )

    for episode in validation:
        validation_tweets.update(
            get_tweet_ids(episode)
        )

    for episode in test:
        test_tweets.update(
            get_tweet_ids(episode)
        )

    train_validation = (
        train_tweets
        & validation_tweets
    )

    train_test = (
        train_tweets
        & test_tweets
    )

    validation_test = (
        validation_tweets
        & test_tweets
    )

    print()
    print("=" * 60)
    print("TWEET-LEVEL LEAKAGE CHECK")
    print("=" * 60)

    print(
        f"Train tweets:          "
        f"{len(train_tweets):,}"
    )

    print(
        f"Validation tweets:     "
        f"{len(validation_tweets):,}"
    )

    print(
        f"Test tweets:           "
        f"{len(test_tweets):,}"
    )

    print(
        f"Train ∩ Validation:    "
        f"{len(train_validation):,}"
    )

    print(
        f"Train ∩ Test:          "
        f"{len(train_test):,}"
    )

    print(
        f"Validation ∩ Test:     "
        f"{len(validation_test):,}"
    )

    print("=" * 60)

    if train_validation:
        raise RuntimeError(
            "LEAKAGE DETECTED: "
            "tweet overlap between train and validation."
        )

    if train_test:
        raise RuntimeError(
            "LEAKAGE DETECTED: "
            "tweet overlap between train and test."
        )

    if validation_test:
        raise RuntimeError(
            "LEAKAGE DETECTED: "
            "tweet overlap between validation and test."
        )

    print(
        "PASS: No tweet overlap detected."
    )


def calculate_customer_overlap(
    train,
    validation,
    test,
):
    """
    Calculate customer overlap for reporting.

    Customer overlap is not automatically considered leakage
    here because a TWCS reply chain can contain multiple
    customer accounts.

    We report it transparently instead.
    """

    train_customers = set()

    validation_customers = set()

    test_customers = set()

    for episode in train:
        train_customers.update(
            get_customer_ids(episode)
        )

    for episode in validation:
        validation_customers.update(
            get_customer_ids(episode)
        )

    for episode in test:
        test_customers.update(
            get_customer_ids(episode)
        )

    train_validation = (
        train_customers
        & validation_customers
    )

    train_test = (
        train_customers
        & test_customers
    )

    validation_test = (
        validation_customers
        & test_customers
    )

    print()
    print("=" * 60)
    print("CUSTOMER OVERLAP REPORT")
    print("=" * 60)

    print(
        f"Train customers:       "
        f"{len(train_customers):,}"
    )

    print(
        f"Validation customers:  "
        f"{len(validation_customers):,}"
    )

    print(
        f"Test customers:        "
        f"{len(test_customers):,}"
    )

    print(
        f"Train ∩ Validation:    "
        f"{len(train_validation):,}"
    )

    print(
        f"Train ∩ Test:          "
        f"{len(train_test):,}"
    )

    print(
        f"Validation ∩ Test:     "
        f"{len(validation_test):,}"
    )

    print("=" * 60)

    return {
        "train_validation": len(
            train_validation
        ),
        "train_test": len(
            train_test
        ),
        "validation_test": len(
            validation_test
        ),
    }


def get_date_range(episodes):
    """
    Get the true chronological range of episode start dates.

    TWCS timestamps look like:
        Fri Oct 20 02:29:56 +0000 2017

    We must parse them before comparing them.
    """

    from datetime import datetime

    timestamps = []

    for episode in episodes:

        turns = episode.get(
            "turns",
            []
        )

        if not turns:
            continue

        timestamp = turns[0].get(
            "created_at"
        )

        if not timestamp:
            continue

        try:
            parsed = datetime.strptime(
                timestamp,
                "%a %b %d %H:%M:%S %z %Y"
            )

            timestamps.append(parsed)

        except ValueError:
            continue

    if not timestamps:

        return {
            "earliest": None,
            "latest": None,
        }

    return {
        "earliest": min(timestamps).isoformat(),
        "latest": max(timestamps).isoformat(),
    }

def save_jsonl(
    episodes,
    path,
):
    """
    Save episodes as JSONL.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        for episode in episodes:

            f.write(
                json.dumps(
                    episode,
                    ensure_ascii=False
                )
                + "\n"
            )

    print(
        f"Saved {len(episodes):,} episodes "
        f"to {path}"
    )


def create_summary(
    train,
    validation,
    test,
    seed,
    customer_overlap,
):
    """
    Create reproducibility metadata.
    """

    return {
        "seed": seed,

        "split_method": (
            "random episode-level split"
        ),

        "ratios": {
            "train": 0.70,
            "validation": 0.15,
            "test": 0.15,
        },

        "episodes": {
            "total": (
                len(train)
                + len(validation)
                + len(test)
            ),
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },

        "date_ranges": {
            "train": get_date_range(train),
            "validation": get_date_range(
                validation
            ),
            "test": get_date_range(test),
        },

        "customer_overlap": customer_overlap,

        "tweet_overlap": {
            "train_validation": 0,
            "train_test": 0,
            "validation_test": 0,
        },
    }


def split_dataset(
    input_path,
    output_dir=(
        "data/processed/splits"
    ),
    seed=42,
):
    """
    Create leakage-safe train/validation/test
    episode splits.
    """

    episodes = load_episodes(
        input_path
    )

    if not episodes:

        raise RuntimeError(
            "No episodes found."
        )

    # ---------------------------------------------------------
    # Split complete episodes.
    # ---------------------------------------------------------

    train, validation, test = split_episodes(
        episodes,
        train_ratio=0.70,
        validation_ratio=0.15,
        test_ratio=0.15,
        seed=seed,
    )

    print()
    print("=" * 60)
    print("EPISODE SPLIT")
    print("=" * 60)

    print(
        f"Total episodes:       "
        f"{len(episodes):,}"
    )

    print(
        f"Train episodes:       "
        f"{len(train):,}"
    )

    print(
        f"Validation episodes:  "
        f"{len(validation):,}"
    )

    print(
        f"Test episodes:        "
        f"{len(test):,}"
    )

    print("=" * 60)

    # ---------------------------------------------------------
    # Primary leakage check.
    # ---------------------------------------------------------

    verify_tweet_overlap(
        train,
        validation,
        test,
    )

    # ---------------------------------------------------------
    # Customer overlap reporting.
    # ---------------------------------------------------------

    customer_overlap = (
        calculate_customer_overlap(
            train,
            validation,
            test,
        )
    )

    # ---------------------------------------------------------
    # Save.
    # ---------------------------------------------------------

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    save_jsonl(
        train,
        output_dir / "train.jsonl"
    )

    save_jsonl(
        validation,
        output_dir / "validation.jsonl"
    )

    save_jsonl(
        test,
        output_dir / "test.jsonl"
    )

    # ---------------------------------------------------------
    # Save summary.
    # ---------------------------------------------------------

    summary = create_summary(
        train=train,
        validation=validation,
        test=test,
        seed=seed,
        customer_overlap=customer_overlap,
    )

    summary_path = (
        output_dir
        / "split_summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            summary,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(
        f"Summary saved to "
        f"{summary_path}"
    )

    return train, validation, test


if __name__ == "__main__":

    input_path = os.getenv(
        "EPISODES_PATH",
        "data/processed/"
        "amazonhelp_episodes.jsonl"
    )

    output_dir = os.getenv(
        "SPLITS_PATH",
        "data/processed/splits"
    )

    seed = int(
        os.getenv(
            "SPLIT_SEED",
            "42"
        )
    )

    if not Path(input_path).exists():

        print(
            f"Episode file not found: "
            f"{input_path}"
        )

        print(
            "Run conversations.py first."
        )

        raise SystemExit(1)

    split_dataset(
        input_path=input_path,
        output_dir=output_dir,
        seed=seed,
    )