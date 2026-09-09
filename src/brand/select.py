import pandas as pd
from pathlib import Path


def select_candidates(summary_csv, raw_csv):
    """
    Select practical candidate support brands from TWCS.

    The dataset does not contain an explicit resolution label.
    Therefore, the metrics below are observable interaction
    proxies and must not be interpreted as true resolution rates.
    """

    print("Loading brand summary...")
    summary = pd.read_csv(summary_csv)

    print("Loading raw dataset...")

    df = pd.read_csv(
        raw_csv,
        usecols=[
            "tweet_id",
            "author_id",
            "inbound",
            "in_response_to_tweet_id",
        ],
        dtype={
            "tweet_id": "string",
            "author_id": "string",
            "in_response_to_tweet_id": "string",
        },
    )

    # ---------------------------------------------------------
    # Normalize IDs
    # ---------------------------------------------------------

    for col in ["tweet_id", "in_response_to_tweet_id"]:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )

    df["author_id"] = df["author_id"].astype("string").str.strip()

    inbound = df[df["inbound"] == True].copy()
    outbound = df[df["inbound"] == False].copy()

    print(f"Total tweets: {len(df):,}")
    print(f"Inbound customer tweets: {len(inbound):,}")
    print(f"Outbound support tweets: {len(outbound):,}")

    # ---------------------------------------------------------
    # Candidate brands
    # ---------------------------------------------------------

    candidates = summary["brand"].astype(str).tolist()

    results = []

    for brand in candidates:

        brand_outbound = outbound[
            outbound["author_id"] == brand
        ]

        tweet_count = len(brand_outbound)

        if tweet_count == 0:
            continue

        # Support tweets that are replies.
        replies = brand_outbound[
            brand_outbound["in_response_to_tweet_id"].notna()
        ].copy()

        support_replies = len(replies)

        # -----------------------------------------------------
        # Find the actual customer tweets being replied to.
        #
        # support.in_response_to_tweet_id
        #                ↓
        # customer.tweet_id
        # -----------------------------------------------------

        replied_ids = replies[
            "in_response_to_tweet_id"
        ].dropna().drop_duplicates()

        customer_tweets = inbound[
            inbound["tweet_id"].isin(replied_ids)
        ]

        unique_customers = customer_tweets[
            "author_id"
        ].nunique()

        reply_rate = (
            support_replies / tweet_count
            if tweet_count > 0
            else 0
        )

        results.append(
            {
                "brand": brand,
                "tweet_count": tweet_count,
                "support_replies": support_replies,
                "unique_customers": unique_customers,
                "reply_rate": reply_rate,
            }
        )

    result_df = pd.DataFrame(results)

    # ---------------------------------------------------------
    # Require enough support interactions
    # ---------------------------------------------------------

    eligible = result_df[
        result_df["support_replies"] >= 1000
    ].copy()

    # ---------------------------------------------------------
    # Normalize ranking signals
    # ---------------------------------------------------------

    ranking_columns = [
        "support_replies",
        "unique_customers",
        "tweet_count",
        "reply_rate",
    ]

    for col in ranking_columns:

        minimum = eligible[col].min()
        maximum = eligible[col].max()

        if maximum > minimum:
            eligible[f"{col}_norm"] = (
                eligible[col] - minimum
            ) / (maximum - minimum)
        else:
            eligible[f"{col}_norm"] = 0.0

    # ---------------------------------------------------------
    # Practical candidate score
    # ---------------------------------------------------------

    eligible["candidate_score"] = (
        0.40 * eligible["support_replies_norm"]
        + 0.25 * eligible["unique_customers_norm"]
        + 0.20 * eligible["reply_rate_norm"]
        + 0.15 * eligible["tweet_count_norm"]
    )

    eligible = eligible.sort_values(
        "candidate_score",
        ascending=False,
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    output_dir = Path("results/brand_selection")
    output_dir.mkdir(parents=True, exist_ok=True)

    result_df.sort_values(
        "support_replies",
        ascending=False,
    ).to_csv(
        output_dir / "all_candidate_brands.csv",
        index=False,
    )

    eligible.to_csv(
        output_dir / "candidate_brands.csv",
        index=False,
    )

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    display_columns = [
        "brand",
        "tweet_count",
        "support_replies",
        "unique_customers",
        "reply_rate",
        "candidate_score",
    ]

    print("\n--- Candidate Brand Comparison ---\n")

    print(
        eligible[display_columns]
        .head(15)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # Recommendation file
    # ---------------------------------------------------------

    with open(
        output_dir / "recommendation.md",
        "w",
        encoding="utf-8",
    ) as f:

        f.write("# Brand Selection Recommendation\n\n")

        f.write(
            "Candidate brands are ranked using observable "
            "interaction signals from the Customer Support on "
            "Twitter dataset.\n\n"
        )

        f.write(
            "**Important:** the dataset does not provide an "
            "explicit resolution label. These metrics therefore "
            "represent observable interaction proxies rather "
            "than ground-truth resolution rates.\n\n"
        )

        f.write("## Ranking signals\n\n")
        f.write("- Support reply volume: 40%\n")
        f.write("- Unique customers: 25%\n")
        f.write("- Observable reply rate: 20%\n")
        f.write("- Total support tweet volume: 15%\n\n")

        f.write("## Candidate ranking\n\n")

        f.write(
            eligible[display_columns]
            .head(15)
            .to_markdown(index=False)
        )

        f.write("\n\n## Top 3 candidates\n\n")

        for _, row in eligible.head(3).iterrows():

            f.write(f"### {row['brand']}\n\n")

            f.write(
                f"- Support tweets: "
                f"{int(row['tweet_count']):,}\n"
            )

            f.write(
                f"- Support replies: "
                f"{int(row['support_replies']):,}\n"
            )

            f.write(
                f"- Unique customers: "
                f"{int(row['unique_customers']):,}\n"
            )

            f.write(
                f"- Observable reply rate: "
                f"{row['reply_rate']:.2%}\n"
            )

            f.write(
                f"- Candidate score: "
                f"{row['candidate_score']:.3f}\n\n"
            )

    print(
        f"\nResults saved to: {output_dir}"
    )


if __name__ == "__main__":

    summary_csv = "results/data_profile/brand_summary.csv"
    raw_csv = "data/raw/twcs/twcs.csv"

    if not Path(summary_csv).exists():

        print(
            f"Summary not found at {summary_csv}. "
            "Run profile.py first."
        )

    elif not Path(raw_csv).exists():

        print(
            f"Dataset not found at {raw_csv}. "
            "Run download.py first."
        )

    else:

        select_candidates(
            summary_csv,
            raw_csv,
        )