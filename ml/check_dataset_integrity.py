"""
One-time integrity scan for a SpoofDataset-style index CSV.

Run this BEFORE deciding whether to redownload anything. It tells you:
  - exactly how many files are actually unreadable
  - the real exception for each failure (grouped, so you see patterns:
    e.g. "all failures are 0-byte files" vs "all failures are a specific
    codec error" vs "scattered / random" -- each points to a different
    root cause)
  - writes a cleaned CSV you can train on immediately while you investigate

Uses soundfile directly (what librosa uses under the hood for flac) rather
than the full librosa.load() + resample + mel-spectrogram path, so this
scan is much faster than actually running the training pipeline.

Usage:
    python check_dataset_integrity.py ml/data/protocols/asvspoof2021_la_index.csv
"""
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import soundfile as sf


def scan(csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    total = len(df)
    print(f"Scanning {total:,} files listed in {csv_path} ...\n")

    bad_rows = []
    error_types = Counter()
    zero_byte_count = 0
    missing_count = 0

    for i, row in df.iterrows():
        filepath = Path(row["filepath"])

        if not filepath.exists():
            missing_count += 1
            error_types["FileNotFoundError (path in CSV, not on disk)"] += 1
            bad_rows.append(row)
            continue

        if filepath.stat().st_size == 0:
            zero_byte_count += 1
            error_types["Zero-byte file"] += 1
            bad_rows.append(row)
            continue

        try:
            # Reading just the header + a short block is enough to catch
            # truncated/corrupt files without decoding the whole thing.
            with sf.SoundFile(str(filepath)) as f:
                f.read(frames=1024)
        except Exception as e:
            error_types[f"{type(e).__name__}: {str(e)[:80]}"] += 1
            bad_rows.append(row)

        if (i + 1) % 20000 == 0:
            print(f"  ...{i + 1:,}/{total:,} checked")

    good = total - len(bad_rows)
    print(f"\n{'=' * 60}")
    print(f"  Integrity scan results")
    print(f"{'=' * 60}")
    print(f"  Total listed:    {total:,}")
    print(f"  Readable:        {good:,} ({100 * good / total:.2f}%)")
    print(f"  Unreadable:      {len(bad_rows):,} ({100 * len(bad_rows) / total:.2f}%)")
    print(f"    - missing from disk: {missing_count:,}")
    print(f"    - zero-byte:         {zero_byte_count:,}")
    print(f"    - other read errors: {len(bad_rows) - missing_count - zero_byte_count:,}")

    if error_types:
        print(f"\n  Error breakdown (top 10):")
        for msg, count in error_types.most_common(10):
            print(f"    {count:>6,}  {msg}")

    # Write a cleaned CSV you can train on right away
    bad_paths = {str(r["filepath"]) for r in bad_rows}
    clean_df = df[~df["filepath"].astype(str).isin(bad_paths)]
    clean_path = Path(csv_path).with_name(Path(csv_path).stem + "_clean.csv")
    clean_df.to_csv(clean_path, index=False)
    print(f"\n  Clean CSV written to: {clean_path}")
    print(f"  ({len(clean_df):,} usable rows)")

    # Interpretation hint
    bad_pct = 100 * len(bad_rows) / total
    print(f"\n{'=' * 60}")
    if bad_pct < 0.5:
        print("  Verdict: a small, normal amount of bad files for a corpus this")
        print("  size. Safe to just train on the _clean.csv and move on --")
        print("  redownloading is very unlikely to be worth it.")
    elif bad_pct < 5:
        print("  Verdict: elevated but not catastrophic. Worth spot-checking a")
        print("  few of the failed files by hand before deciding to redownload.")
    else:
        print("  Verdict: high failure rate. This strongly suggests an incomplete")
        print("  or corrupted download rather than a handful of bad files --")
        print("  redownloading from the official source is the right call.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_dataset_integrity.py <path_to_index_csv>")
        sys.exit(1)
    scan(sys.argv[1])
