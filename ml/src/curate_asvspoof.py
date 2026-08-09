"""
ASVspoof 2021 Dataset Curation Script
======================================
Parses the official ASVspoof2021 trial_metadata.txt protocol files for all
three tracks (LA, DF, PA), resolves each file_id to its absolute .flac path,
validates existence on disk, and writes clean CSVs ready for training.

Output CSV format (matches dataset_loader.py SpoofDataset expectations):
    filepath,label
    C:/.../LA_E_9332881.flac,spoof
    C:/.../LA_E_5464494.flac,bonafide

Usage:
    python curate_asvspoof.py
"""

import os
import csv
import sys
from pathlib import Path
from collections import Counter

# ---------------------------------------------------------------------------
# Configuration — all paths relative to the project root
# ---------------------------------------------------------------------------
# Base directory for raw ASVspoof data
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Output directory for curated CSVs
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "protocols"

# Track definitions: metadata path, audio directories, label column index
TRACKS = {
    "LA": {
        "metadata": RAW_DIR / "keys" / "LA" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_LA_eval" / "flac",
        ],
        "label_col": 5,  # 0-indexed column for bonafide/spoof label
    },
    "DF": {
        "metadata": RAW_DIR / "keys" / "DF" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_DF_eval" / "flac",
        ],
        "label_col": 5,
    },
    "PA": {
        "metadata": RAW_DIR / "PA-keys-full" / "keys" / "PA" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_PA_eval_part00" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part01" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part02" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part03" / "ASVspoof2021_PA_eval" / "flac",
        ],
        "label_col": 9,  # PA has more room/mic config columns before the label
    },
}


def build_file_index(audio_dirs):
    """
    Build a dict mapping file_id (stem, no extension) → absolute path
    for all .flac files found across the given directories.
    """
    index = {}
    for audio_dir in audio_dirs:
        if not audio_dir.exists():
            print(f"  [WARNING] Audio directory not found: {audio_dir}")
            continue
        for flac_file in audio_dir.glob("*.flac"):
            file_id = flac_file.stem  # e.g. "LA_E_9332881"
            index[file_id] = str(flac_file.resolve())
    return index


def parse_metadata(metadata_path, label_col):
    """
    Parse the trial_metadata.txt file.
    Returns a list of (file_id, label) tuples.
    Deduplicates by file_id (some metadata files may have repeated entries
    for the same file_id with consistent labels).
    """
    entries = {}
    duplicates = 0

    with open(metadata_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()

            if len(parts) <= label_col:
                print(f"  [WARNING] Line {line_num}: not enough columns "
                      f"(got {len(parts)}, need {label_col + 1}): {line[:80]}...")
                continue

            file_id = parts[1]
            label = parts[label_col].lower()

            if label not in ("bonafide", "spoof"):
                print(f"  [WARNING] Line {line_num}: unexpected label '{label}' "
                      f"for {file_id}, skipping")
                continue

            if file_id in entries:
                duplicates += 1
                # Keep the first occurrence (they should be consistent)
            else:
                entries[file_id] = label

    if duplicates > 0:
        print(f"  [INFO] {duplicates} duplicate file_id entries found and deduplicated")

    return entries


def curate_track(track_name, track_config):
    """
    Full curation pipeline for a single ASVspoof track.
    Returns stats dict.
    """
    print(f"\n{'='*60}")
    print(f"  Curating ASVspoof 2021 — {track_name} track")
    print(f"{'='*60}")

    metadata_path = track_config["metadata"]
    audio_dirs = track_config["audio_dirs"]
    label_col = track_config["label_col"]

    # Step 1: Validate metadata file exists
    if not metadata_path.exists():
        print(f"  [ERROR] Metadata file not found: {metadata_path}")
        return None

    print(f"  Metadata: {metadata_path}")
    print(f"  Audio dirs: {len(audio_dirs)} directories")

    # Step 2: Build file index from audio directories
    print(f"\n  [1/4] Building audio file index...")
    file_index = build_file_index(audio_dirs)
    print(f"        Found {len(file_index):,} .flac files on disk")

    # Step 3: Parse metadata
    print(f"  [2/4] Parsing metadata labels...")
    metadata_entries = parse_metadata(metadata_path, label_col)
    print(f"        Found {len(metadata_entries):,} unique file_id entries in metadata")

    # Step 4: Join metadata with file paths (inner join — only include files
    # that BOTH have a label AND exist on disk)
    print(f"  [3/4] Joining labels with audio file paths...")
    rows = []
    missing_audio = 0
    label_counts = Counter()

    for file_id, label in metadata_entries.items():
        if file_id in file_index:
            filepath = file_index[file_id]
            rows.append({"filepath": filepath, "label": label})
            label_counts[label] += 1
        else:
            missing_audio += 1

    # Also check for orphan audio files (on disk but not in metadata)
    orphan_audio = len(file_index) - (len(rows))

    print(f"        Matched: {len(rows):,} files")
    print(f"        Missing audio (in metadata but no .flac): {missing_audio:,}")
    print(f"        Orphan audio (on disk but not in metadata): {orphan_audio:,}")
    print(f"        Label distribution: {dict(label_counts)}")

    # Step 5: Write output CSV
    output_path = OUTPUT_DIR / f"asvspoof2021_{track_name.lower()}_index.csv"
    print(f"  [4/4] Writing curated CSV to {output_path}...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filepath", "label"])
        writer.writeheader()
        writer.writerows(rows)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"        Done! {len(rows):,} rows written ({file_size_mb:.2f} MB)")

    return {
        "track": track_name,
        "total_matched": len(rows),
        "bonafide": label_counts.get("bonafide", 0),
        "spoof": label_counts.get("spoof", 0),
        "missing_audio": missing_audio,
        "orphan_audio": orphan_audio,
        "output_csv": str(output_path),
    }


def write_combined_csv(track_stats):
    """
    Optionally write a combined CSV merging all tracks for convenience.
    Only includes tracks that were successfully curated.
    """
    combined_path = OUTPUT_DIR / "asvspoof2021_combined_index.csv"
    print(f"\n{'='*60}")
    print(f"  Writing combined index CSV")
    print(f"{'='*60}")

    total_rows = 0
    with open(combined_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=["filepath", "label", "track"])
        writer.writeheader()

        for stats in track_stats:
            if stats is None:
                continue
            track_csv = stats["output_csv"]
            track_name = stats["track"]
            with open(track_csv, "r", encoding="utf-8") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    row["track"] = track_name
                    writer.writerow(row)
                    total_rows += 1

    file_size_mb = combined_path.stat().st_size / (1024 * 1024)
    print(f"  Combined CSV: {total_rows:,} total rows ({file_size_mb:.2f} MB)")
    print(f"  Saved to: {combined_path}")
    return str(combined_path)


def print_summary(all_stats, combined_csv_path):
    """Print a final human-readable summary."""
    print(f"\n{'='*60}")
    print(f"  ASVspoof 2021 Curation Summary")
    print(f"{'='*60}")
    print(f"  {'Track':<6} {'Bonafide':>10} {'Spoof':>10} {'Total':>10} {'Missing':>10}")
    print(f"  {'-'*6:<6} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10}")

    grand_bonafide = 0
    grand_spoof = 0
    grand_total = 0

    for stats in all_stats:
        if stats is None:
            continue
        print(f"  {stats['track']:<6} {stats['bonafide']:>10,} {stats['spoof']:>10,} "
              f"{stats['total_matched']:>10,} {stats['missing_audio']:>10,}")
        grand_bonafide += stats["bonafide"]
        grand_spoof += stats["spoof"]
        grand_total += stats["total_matched"]

    print(f"  {'-'*6:<6} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10}")
    print(f"  {'TOTAL':<6} {grand_bonafide:>10,} {grand_spoof:>10,} {grand_total:>10,}")

    print(f"\n  Output CSVs:")
    for stats in all_stats:
        if stats is None:
            continue
        print(f"    {stats['track']}: {stats['output_csv']}")
    print(f"    Combined: {combined_csv_path}")

    print(f"\n  Next step: plug any of these CSVs into dataset_loader.py's")
    print(f"  SpoofDataset(csv_path=...) and start training!")
    print(f"{'='*60}\n")


def main():
    print("\nASVspoof 2021 Dataset Curation")
    print(f"Raw data directory: {RAW_DIR}")
    print(f"Output directory:   {OUTPUT_DIR}")

    # Curate each track
    all_stats = []
    for track_name, track_config in TRACKS.items():
        stats = curate_track(track_name, track_config)
        all_stats.append(stats)

    # Write combined CSV
    combined_csv_path = write_combined_csv(all_stats)

    # Print summary
    print_summary(all_stats, combined_csv_path)


if __name__ == "__main__":
    main()

"""
ASVspoof 2021 Dataset Curation Script
======================================
Parses the official ASVspoof2021 trial_metadata.txt protocol files for all
three tracks (LA, DF, PA), resolves each file_id to its absolute .flac path,
validates existence on disk, and writes clean CSVs ready for training.

Output CSV format (matches dataset_loader.py SpoofDataset expectations):
    filepath,label
    C:/.../LA_E_9332881.flac,spoof
    C:/.../LA_E_5464494.flac,bonafide

Usage:
    python curate_asvspoof.py
"""

import os
import csv
import sys
from pathlib import Path
from collections import Counter

# ---------------------------------------------------------------------------
# Configuration — all paths relative to the project root
# ---------------------------------------------------------------------------
# Base directory for raw ASVspoof data
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Output directory for curated CSVs
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "protocols"

# Track definitions: metadata path, audio directories, label column index
TRACKS = {
    "LA": {
        "metadata": RAW_DIR / "LA-keys-full" / "keys" / "LA" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_LA_eval" / "ASVspoof2021_LA_eval" / "flac",
        ],
        "label_col": 5,  # 0-indexed column for bonafide/spoof label
    },
    "DF": {
        "metadata": RAW_DIR / "DF-keys-full" / "keys" / "DF" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_DF_eval_part00" / "ASVspoof2021_DF_eval" / "flac",
            RAW_DIR / "ASVspoof2021_DF_eval_part01" / "ASVspoof2021_DF_eval" / "flac",
            RAW_DIR / "ASVspoof2021_DF_eval_part02" / "ASVspoof2021_DF_eval" / "flac",
        ],
        "label_col": 5,
    },
    "PA": {
        "metadata": RAW_DIR / "PA-keys-full" / "keys" / "PA" / "CM" / "trial_metadata.txt",
        "audio_dirs": [
            RAW_DIR / "ASVspoof2021_PA_eval_part00" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part01" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part02" / "ASVspoof2021_PA_eval" / "flac",
            RAW_DIR / "ASVspoof2021_PA_eval_part03" / "ASVspoof2021_PA_eval" / "flac",
        ],
        "label_col": 9,  # PA has more room/mic config columns before the label
    },
}


def build_file_index(audio_dirs):
    """
    Build a dict mapping file_id (stem, no extension) → absolute path
    for all .flac files found across the given directories.
    """
    index = {}
    for audio_dir in audio_dirs:
        if not audio_dir.exists():
            print(f"  [WARNING] Audio directory not found: {audio_dir}")
            continue
        for flac_file in audio_dir.glob("*.flac"):
            file_id = flac_file.stem  # e.g. "LA_E_9332881"
            index[file_id] = str(flac_file.resolve())
    return index


def parse_metadata(metadata_path, label_col):
    """
    Parse the trial_metadata.txt file.
    Returns a list of (file_id, label) tuples.
    Deduplicates by file_id (some metadata files may have repeated entries
    for the same file_id with consistent labels).
    """
    entries = {}
    duplicates = 0

    with open(metadata_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()

            if len(parts) <= label_col:
                print(f"  [WARNING] Line {line_num}: not enough columns "
                      f"(got {len(parts)}, need {label_col + 1}): {line[:80]}...")
                continue

            file_id = parts[1]
            label = parts[label_col].lower()

            if label not in ("bonafide", "spoof"):
                print(f"  [WARNING] Line {line_num}: unexpected label '{label}' "
                      f"for {file_id}, skipping")
                continue

            if file_id in entries:
                duplicates += 1
                # Keep the first occurrence (they should be consistent)
            else:
                entries[file_id] = label

    if duplicates > 0:
        print(f"  [INFO] {duplicates} duplicate file_id entries found and deduplicated")

    return entries


def curate_track(track_name, track_config):
    """
    Full curation pipeline for a single ASVspoof track.
    Returns stats dict.
    """
    print(f"\n{'='*60}")
    print(f"  Curating ASVspoof 2021 — {track_name} track")
    print(f"{'='*60}")

    metadata_path = track_config["metadata"]
    audio_dirs = track_config["audio_dirs"]
    label_col = track_config["label_col"]

    # Step 1: Validate metadata file exists
    if not metadata_path.exists():
        print(f"  [ERROR] Metadata file not found: {metadata_path}")
        return None

    print(f"  Metadata: {metadata_path}")
    print(f"  Audio dirs: {len(audio_dirs)} directories")

    # Step 2: Build file index from audio directories
    print(f"\n  [1/4] Building audio file index...")
    file_index = build_file_index(audio_dirs)
    print(f"        Found {len(file_index):,} .flac files on disk")

    # Step 3: Parse metadata
    print(f"  [2/4] Parsing metadata labels...")
    metadata_entries = parse_metadata(metadata_path, label_col)
    print(f"        Found {len(metadata_entries):,} unique file_id entries in metadata")

    # Step 4: Join metadata with file paths (inner join — only include files
    # that BOTH have a label AND exist on disk)
    print(f"  [3/4] Joining labels with audio file paths...")
    rows = []
    missing_audio = 0
    label_counts = Counter()

    for file_id, label in metadata_entries.items():
        if file_id in file_index:
            filepath = file_index[file_id]
            rows.append({"filepath": filepath, "label": label})
            label_counts[label] += 1
        else:
            missing_audio += 1

    # Also check for orphan audio files (on disk but not in metadata)
    orphan_audio = len(file_index) - (len(rows))

    print(f"        Matched: {len(rows):,} files")
    print(f"        Missing audio (in metadata but no .flac): {missing_audio:,}")
    print(f"        Orphan audio (on disk but not in metadata): {orphan_audio:,}")
    print(f"        Label distribution: {dict(label_counts)}")

    # Step 5: Write output CSV
    output_path = OUTPUT_DIR / f"asvspoof2021_{track_name.lower()}_index.csv"
    print(f"  [4/4] Writing curated CSV to {output_path}...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filepath", "label"])
        writer.writeheader()
        writer.writerows(rows)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"        Done! {len(rows):,} rows written ({file_size_mb:.2f} MB)")

    return {
        "track": track_name,
        "total_matched": len(rows),
        "bonafide": label_counts.get("bonafide", 0),
        "spoof": label_counts.get("spoof", 0),
        "missing_audio": missing_audio,
        "orphan_audio": orphan_audio,
        "output_csv": str(output_path),
    }


def write_combined_csv(track_stats):
    """
    Optionally write a combined CSV merging all tracks for convenience.
    Only includes tracks that were successfully curated.
    """
    combined_path = OUTPUT_DIR / "asvspoof2021_combined_index.csv"
    print(f"\n{'='*60}")
    print(f"  Writing combined index CSV")
    print(f"{'='*60}")

    total_rows = 0
    with open(combined_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=["filepath", "label", "track"])
        writer.writeheader()

        for stats in track_stats:
            if stats is None:
                continue
            track_csv = stats["output_csv"]
            track_name = stats["track"]
            with open(track_csv, "r", encoding="utf-8") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    row["track"] = track_name
                    writer.writerow(row)
                    total_rows += 1

    file_size_mb = combined_path.stat().st_size / (1024 * 1024)
    print(f"  Combined CSV: {total_rows:,} total rows ({file_size_mb:.2f} MB)")
    print(f"  Saved to: {combined_path}")
    return str(combined_path)


def print_summary(all_stats, combined_csv_path):
    """Print a final human-readable summary."""
    print(f"\n{'='*60}")
    print(f"  ASVspoof 2021 Curation Summary")
    print(f"{'='*60}")
    print(f"  {'Track':<6} {'Bonafide':>10} {'Spoof':>10} {'Total':>10} {'Missing':>10}")
    print(f"  {'-'*6:<6} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10}")

    grand_bonafide = 0
    grand_spoof = 0
    grand_total = 0

    for stats in all_stats:
        if stats is None:
            continue
        print(f"  {stats['track']:<6} {stats['bonafide']:>10,} {stats['spoof']:>10,} "
              f"{stats['total_matched']:>10,} {stats['missing_audio']:>10,}")
        grand_bonafide += stats["bonafide"]
        grand_spoof += stats["spoof"]
        grand_total += stats["total_matched"]

    print(f"  {'-'*6:<6} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10}")
    print(f"  {'TOTAL':<6} {grand_bonafide:>10,} {grand_spoof:>10,} {grand_total:>10,}")

    print(f"\n  Output CSVs:")
    for stats in all_stats:
        if stats is None:
            continue
        print(f"    {stats['track']}: {stats['output_csv']}")
    print(f"    Combined: {combined_csv_path}")

    print(f"\n  Next step: plug any of these CSVs into dataset_loader.py's")
    print(f"  SpoofDataset(csv_path=...) and start training!")
    print(f"{'='*60}\n")


def main():
    print("\nASVspoof 2021 Dataset Curation")
    print(f"Raw data directory: {RAW_DIR}")
    print(f"Output directory:   {OUTPUT_DIR}")

    # Curate each track
    all_stats = []
    for track_name, track_config in TRACKS.items():
        stats = curate_track(track_name, track_config)
        all_stats.append(stats)

    # Write combined CSV
    combined_csv_path = write_combined_csv(all_stats)

    # Print summary
    print_summary(all_stats, combined_csv_path)


if __name__ == "__main__":
    main()
