import pandas as pd
import soundfile as sf
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
import warnings

# Suppress soundfile warnings about chunk sizes
warnings.filterwarnings("ignore")

def is_valid_audio(filepath):
    # Check if file exists and is not empty
    if not os.path.exists(filepath):
        return False
    if os.path.getsize(filepath) == 0:
        return False
    
    # Try reading the entire file to catch deep corruption (e.g. lost sync)
    try:
        # Just info() only checks headers. We need to read the data.
        data, samplerate = sf.read(filepath)
        return True
    except Exception:
        return False

def check_dataset(csv_path):
    print(f"\nLoading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    total_files = len(df)
    print(f"Checking {total_files:,} files for corruption (this may take a moment)...")
    
    # Use ThreadPoolExecutor for fast parallel checking
    results = []
    with ThreadPoolExecutor(max_workers=32) as executor:
        for idx, is_valid in enumerate(executor.map(is_valid_audio, df['filepath'])):
            results.append(is_valid)
            if (idx + 1) % 50000 == 0:
                print(f"  ... checked {idx + 1:,}/{total_files:,} files")
        
    df_clean = df[results]
    corrupted_count = total_files - len(df_clean)
    
    print(f"\nResult: Found {corrupted_count:,} corrupted/missing files.")
    
    if corrupted_count > 0:
        clean_csv_path = csv_path.replace(".csv", "_clean.csv")
        df_clean.to_csv(clean_csv_path, index=False)
        print(f"Saved cleaned dataset to {clean_csv_path}")
        print(f"Update your code to use this new _clean.csv file.")
    else:
        print("No corrupted files found. Your CSV is good to go!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check dataset CSV for corrupted audio files.")
    parser.add_argument("csv_path", help="Path to the dataset CSV file")
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"Error: {args.csv_path} does not exist.")
    else:
        check_dataset(args.csv_path)
