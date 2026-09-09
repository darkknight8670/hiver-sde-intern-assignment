import pandas as pd
import json
import os
from pathlib import Path
from collections import defaultdict


def normalize_id(value):
    """
    Normalize Twitter IDs so that values such as:

        123456789
        123456789.0
        "123456789"
        "123456789.0"

    all become:

        "123456789"

    This is important because pandas may load columns containing
    missing IDs as floats.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.endswith(".0"):
        value = value[:-2]

    return value


def load_dataset(csv_path):
    """Load the Twitter customer support dataset."""

    print(f"Loading dataset from {csv_path}...")

    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df):,} tweets.")
    print(f"Columns: {df.columns.tolist()}")

    return df


def build_lookup_maps(df):
    """
    Build tweet lookup and parent -> children relationships.
    """

    print("Building tweet lookup...")

    tweet_map = {}
    children_map = defaultdict(list)

    for row in df.itertuples(index=False):

        tweet_id = normalize_id(row.tweet_id)

        if tweet_id is None:
            continue

        parent_id = normalize_id(
            row.in_response_to_tweet_id
        )

        tweet = {
            "tweet_id": tweet_id,
            "author_id": str(row.author_id),
            "inbound": bool(row.inbound),
            "created_at": str(row.created_at),
            "text": str(row.text),
            "in_response_to_tweet_id": parent_id,
        }

        tweet_map[tweet_id] = tweet

        if parent_id is not None:
            children_map[parent_id].append(tweet_id)

    print(f"Tweet lookup: {len(tweet_map):,}")
    print(
        f"Parent-child relationships: "
        f"{len(children_map):,}"
    )

    return tweet_map, children_map


def get_brand_tweets(df, brand):
    """
    Get all outbound tweets from the selected support brand.
    """

    brand_df = df[
        (df["author_id"].astype(str) == str(brand))
        & (df["inbound"] == False)
    ]

    print(
        f"Support tweets from {brand}: "
        f"{len(brand_df):,}"
    )

    return brand_df


def get_direct_customer_messages(df, brand):
    """
    Find customer tweets that received a direct reply
    from the selected brand.
    """

    brand_df = get_brand_tweets(df, brand)

    # Normalize IDs from the support tweets.
    replied_customer_ids = set(
        brand_df["in_response_to_tweet_id"]
        .dropna()
        .map(normalize_id)
    )

    print(
        f"Unique customer IDs referenced by "
        f"{brand}: {len(replied_customer_ids):,}"
    )

    # Normalize customer tweet IDs before matching.
    customer_ids = df["tweet_id"].map(normalize_id)

    customer_df = df[
        (df["inbound"] == True)
        & customer_ids.isin(replied_customer_ids)
    ]

    print(
        f"Customer messages directly answered: "
        f"{len(customer_df):,}"
    )

    return customer_df


def find_episode_starts(
    customer_df,
    tweet_map,
    brand
):
    """
    Find genuine starts of support episodes.

    If a customer tweet is itself replying to an AmazonHelp
    tweet, it is considered a continuation of that episode,
    not a new episode.

    Example:

        Customer
            ↓
        AmazonHelp
            ↓
        Customer
            ↓
        AmazonHelp

    This becomes ONE episode.
    """

    episode_starts = []

    for row in customer_df.itertuples(index=False):

        customer_id = normalize_id(row.tweet_id)

        if customer_id is None:
            continue

        customer = tweet_map.get(customer_id)

        if customer is None:
            continue

        parent_id = customer[
            "in_response_to_tweet_id"
        ]

        if parent_id is not None:

            parent = tweet_map.get(parent_id)

            if (
                parent is not None
                and parent["author_id"] == str(brand)
                and parent["inbound"] is False
            ):
                # This customer message is replying to
                # AmazonHelp, so it belongs to an existing
                # support episode.
                continue

        episode_starts.append(customer_id)

    print(
        f"Episode start candidates: "
        f"{len(episode_starts):,}"
    )

    return episode_starts


def choose_next_reply(
    current_id,
    expected_speaker,
    tweet_map,
    children_map,
    brand
):
    """
    Find the next valid reply in the conversation.

    After a customer:
        expect AmazonHelp.

    After AmazonHelp:
        expect a customer.
    """

    children = children_map.get(
        current_id,
        []
    )

    valid_children = []

    for child_id in children:

        child = tweet_map.get(child_id)

        if child is None:
            continue

        if expected_speaker == "brand":

            if (
                child["author_id"] == str(brand)
                and child["inbound"] is False
            ):
                valid_children.append(child)

        else:

            if child["inbound"] is True:
                valid_children.append(child)

    if not valid_children:
        return None

    # Choose the earliest reply.
    valid_children.sort(
        key=lambda x: x["created_at"]
    )

    return valid_children[0]


def build_episode(
    start_id,
    tweet_map,
    children_map,
    brand,
    max_turns=50
):
    """
    Build one customer <-> support episode.
    """

    start = tweet_map.get(start_id)

    if start is None:
        return None

    # Every episode must begin with a customer.
    if start["inbound"] is not True:
        return None

    turns = []

    current_id = start_id

    # First reply should be from support.
    expected_speaker = "brand"

    visited = set()

    truncated = False

    while current_id is not None:

        # Protect against malformed cycles.
        if current_id in visited:
            break

        visited.add(current_id)

        current = tweet_map.get(current_id)

        if current is None:
            break

        speaker = (
            "customer"
            if current["inbound"]
            else "support"
        )

        turns.append(
            {
                "tweet_id": current["tweet_id"],
                "speaker": speaker,
                "author": current["author_id"],
                "created_at": current["created_at"],
                "text": current["text"],
            }
        )

        # Safety limit.
        if len(turns) >= max_turns:

            next_reply = choose_next_reply(
                current_id=current_id,
                expected_speaker=expected_speaker,
                tweet_map=tweet_map,
                children_map=children_map,
                brand=brand,
            )

            if next_reply is not None:
                truncated = True

            break

        next_reply = choose_next_reply(
            current_id=current_id,
            expected_speaker=expected_speaker,
            tweet_map=tweet_map,
            children_map=children_map,
            brand=brand,
        )

        if next_reply is None:
            break

        current_id = next_reply["tweet_id"]

        # Alternate speaker.
        if expected_speaker == "brand":
            expected_speaker = "customer"
        else:
            expected_speaker = "brand"

    # Need at least customer + support.
    if len(turns) < 2:
        return None

    customer_turns = [
        t for t in turns
        if t["speaker"] == "customer"
    ]

    support_turns = [
        t for t in turns
        if t["speaker"] == "support"
    ]

    return {
        "episode_id": f"{brand}_{start_id}",
        "brand": brand,
        "start_tweet_id": start_id,

        "num_turns": len(turns),
        "num_customer_turns": len(customer_turns),
        "num_support_turns": len(support_turns),

        "truncated": truncated,

        # This is only a proxy.
        # We do NOT claim that the case was actually resolved.
        "resolution_proxy": {
            "support_replied": len(support_turns) > 0,
            "customer_followup_count": max(
                0,
                len(customer_turns) - 1
            ),
        },

        "turns": turns,
    }


def reconstruct_support_episodes(
    csv_path,
    brand="AmazonHelp",
    output_path=(
        "data/processed/"
        "amazonhelp_episodes.jsonl"
    ),
    max_turns=50,
):
    """
    Complete support episode reconstruction pipeline.
    """

    df = load_dataset(csv_path)

    tweet_map, children_map = build_lookup_maps(df)

    # ---------------------------------------------------------
    # Find customer messages directly answered by AmazonHelp.
    # ---------------------------------------------------------

    customer_df = get_direct_customer_messages(
        df,
        brand
    )

    # ---------------------------------------------------------
    # Find genuine episode starts.
    # ---------------------------------------------------------

    episode_starts = find_episode_starts(
        customer_df,
        tweet_map,
        brand
    )

    print(
        f"Building episodes from "
        f"{len(episode_starts):,} episode starts..."
    )

    # ---------------------------------------------------------
    # Build episodes.
    # ---------------------------------------------------------

    episodes = []

    for i, start_id in enumerate(
        episode_starts
    ):

        episode = build_episode(
            start_id=start_id,
            tweet_map=tweet_map,
            children_map=children_map,
            brand=brand,
            max_turns=max_turns,
        )

        if episode is not None:
            episodes.append(episode)

        if (i + 1) % 10000 == 0:
            print(
                f"Processed "
                f"{i + 1:,}/"
                f"{len(episode_starts):,} starts..."
            )

    # ---------------------------------------------------------
    # Statistics.
    # ---------------------------------------------------------

    multi_turn = [
        e for e in episodes
        if e["num_turns"] > 2
    ]

    truncated_count = sum(
        e["truncated"]
        for e in episodes
    )

    print()
    print("=" * 60)
    print("CONVERSATION RECONSTRUCTION SUMMARY")
    print("=" * 60)

    print(f"Brand:              {brand}")
    print(
        f"Episode starts:     "
        f"{len(episode_starts):,}"
    )
    print(
        f"Valid episodes:     "
        f"{len(episodes):,}"
    )
    print(
        f"Multi-turn:         "
        f"{len(multi_turn):,}"
    )
    print(
        f"Truncated:          "
        f"{truncated_count:,}"
    )

    if episodes:

        turn_counts = [
            e["num_turns"]
            for e in episodes
        ]

        print(
            f"Average turns:      "
            f"{sum(turn_counts) / len(turn_counts):.2f}"
        )

        print(
            f"Max turns:          "
            f"{max(turn_counts)}"
        )

    print("=" * 60)

    # ---------------------------------------------------------
    # Save JSONL.
    # ---------------------------------------------------------

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
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

    print()
    print(
        f"Saved episodes to "
        f"{output_file}"
    )

    # ---------------------------------------------------------
    # Show examples.
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("EXAMPLE EPISODES")
    print("=" * 60)

    for i, episode in enumerate(
        episodes[:5],
        1
    ):

        print()
        print(
            f"--- Episode {i}: "
            f"{episode['episode_id']} ---"
        )

        print(
            f"Turns: "
            f"{episode['num_turns']} | "
            f"Customer: "
            f"{episode['num_customer_turns']} | "
            f"Support: "
            f"{episode['num_support_turns']} | "
            f"Truncated: "
            f"{episode['truncated']}"
        )

        for turn in episode["turns"]:

            text = turn["text"].replace(
                "\n",
                " "
            )

            if len(text) > 250:
                text = text[:250] + "..."

            print(
                f"[{turn['speaker']}] "
                f"{text}"
            )

    return episodes


if __name__ == "__main__":

    csv_path = os.getenv(
        "DATASET_PATH",
        "data/raw/twcs/twcs.csv"
    )

    brand = os.getenv(
        "BRAND",
        "AmazonHelp"
    )

    output_path = os.getenv(
        "EPISODES_PATH",
        "data/processed/"
        "amazonhelp_episodes.jsonl"
    )

    max_turns = int(
        os.getenv(
            "MAX_TURNS",
            "50"
        )
    )

    if not Path(csv_path).exists():

        print(
            f"Dataset not found at "
            f"{csv_path}"
        )

        raise SystemExit(1)

    reconstruct_support_episodes(
        csv_path=csv_path,
        brand=brand,
        output_path=output_path,
        max_turns=max_turns,
    )