import os
import argparse
from pathlib import Path

def setup_kaggle():
    """
    Instructions for setting up Kaggle API.
    """
    print("\n--- Kaggle API Setup ---")
    print("1. Go to https://www.kaggle.com/settings")
    print("2. Click 'Create New API Token' to download kaggle.json")
    print("3. Place kaggle.json in ~/.kaggle/ (Linux/Mac) or C:\\Users\\<User>\\.kaggle\\ (Windows)")
    print("------------------------\n")

def download_dataset():
    """
    Downloads the 'Customer Support on Twitter' dataset from Kaggle.
    """
    dataset_slug = "thoughtvector/customer-support-on-twitter"
    target_dir = Path("data/raw")
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        import kaggle
        print(f"Downloading {dataset_slug}...")
        kaggle.api.dataset_download_files(
            dataset_slug,
            path=target_dir,
            unzip=True
        )
        print(f"Dataset downloaded and unzipped to {target_dir}")
    except Exception as e:
        print(f"Error downloading via Kaggle API: {e}")
        print("\nManual Download Instructions:")
        print(f"1. Visit https://www.kaggle.com/datasets/{dataset_slug}")
        print("2. Download the 'Customer Support on Twitter' dataset.")
        print("3. Extract it so that twcs.csv is available under:")
        print(f"   {target_dir.absolute()}/twcs/twcs.csv")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download dataset from Kaggle.")
    parser.add_argument("--setup", action="store_true", help="Show Kaggle API setup instructions.")
    args = parser.parse_args()

    if args.setup:
        setup_kaggle()
    else:
        download_dataset()
