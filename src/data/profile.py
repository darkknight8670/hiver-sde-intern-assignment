import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
from tqdm import tqdm

def profile_dataset(csv_path):
    """
    Profiles the Twitter Customer Support dataset.
    """
    print(f"Loading dataset from {csv_path}...")
    # Load a sample first to check schema
    df_sample = pd.read_csv(csv_path, nrows=5)
    print("Columns:", df_sample.columns.tolist())

    # Load full dataset (using chunking if necessary, but 2.8M rows usually fits in memory)
    df = pd.read_csv(csv_path)
    
    stats = {
        "total_tweets": len(df),
        "unique_authors": df['author_id'].nunique(),
        "brands": df[df['inbound'] == False]['author_id'].unique().tolist(),
        "missing_values": df.isnull().sum().to_dict()
    }

    # Brand-level analysis
    brand_counts = df[df['inbound'] == False]['author_id'].value_counts()
    stats["top_brands_by_tweet_count"] = brand_counts.head(20).to_dict()

    # Conversation reconstruction (Simplified for profiling)
    # A conversation is a chain of tweets linked by in_response_to_tweet_id
    # We want to find brands with high volume of multi-turn interactions
    
    print("Analyzing brand interactions...")
    brand_stats = []
    for brand in tqdm(brand_counts.index[:50], desc="Profiling top 50 brands"):
        brand_df = df[(df['author_id'] == brand) | (df['text'].str.contains(f"@{brand}", case=False, na=False))]
        
        # Count interactions where brand replied to a customer
        replies_to_customers = df[(df['author_id'] == brand) & (df['in_response_to_tweet_id'].notnull())]
        
        brand_stats.append({
            "brand": brand,
            "tweet_count": int(brand_counts[brand]),
            "replies_to_customers": len(replies_to_customers),
            "unique_customers": df[df['in_response_to_tweet_id'].isin(df[df['author_id'] == brand]['tweet_id'])]['author_id'].nunique()
        })

    brand_analysis_df = pd.DataFrame(brand_stats)
    
    # Save results
    output_dir = Path("results/data_profile")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=4)
        
    brand_analysis_df.to_csv(output_dir / "brand_summary.csv", index=False)
    print(f"Profiling complete. Results saved to {output_dir}")
    return brand_analysis_df

if __name__ == "__main__":
    csv_path = os.getenv("DATASET_PATH", "data/raw/twcs/twcs.csv")
    if Path(csv_path).exists():
        profile_dataset(csv_path)
    else:
        print(f"Dataset not found at {csv_path}. Please download it first.")
