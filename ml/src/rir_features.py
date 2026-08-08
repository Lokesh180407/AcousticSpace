import os
from pathlib import Path
import numpy as np
import librosa
import pandas as pd
from tqdm import tqdm

RIR_ROOT = Path("ml/data/raw/RIRS_NOISES")
OUTPUT_CSV = Path("ml/data/protocols/rir_index.csv")

CATEGORY_MAP = {
    "pointsource_noises": "noise",
    "real_rirs_isotropic_noises": "real_rir",
    "simulated_rirs": "simulated_rir",
}


def estimate_rt60(y, sr):
    energy = y ** 2
    if np.sum(energy) == 0:
        return None
    schroeder = np.cumsum(energy[::-1])[::-1]
    schroeder_db = 10 * np.log10(schroeder / (np.max(schroeder) + 1e-10) + 1e-10)

    idx = np.where((schroeder_db <= -5) & (schroeder_db >= -35))[0]
    if len(idx) < 2:
        return None
    slope, _ = np.polyfit(idx, schroeder_db[idx], 1)
    if slope == 0:
        return None
    rt60 = -60 / slope / sr
    return rt60


def curate_rir_dataset():
    rows = []

    for folder_name, category in CATEGORY_MAP.items():
        folder_path = RIR_ROOT / folder_name
        if not folder_path.exists():
            print(f"WARNING: {folder_path} not found, skipping.")
            continue

        wav_files = list(folder_path.rglob("*.wav"))
        print(f"Found {len(wav_files)} files in {folder_name}")

        for wav_path in tqdm(wav_files, desc=folder_name):
            try:
                y, sr = librosa.load(str(wav_path), sr=16000)
                rt60 = estimate_rt60(y, sr) if category != "noise" else None
                duration = librosa.get_duration(y=y, sr=sr)

                rows.append({
                    "filepath": str(wav_path),
                    "category": category,
                    "subfolder": wav_path.parent.name,
                    "duration_sec": duration,
                    "rt60_sec": rt60,
                })
            except Exception as e:
                print(f"ERROR reading {wav_path}: {e}")

    df = pd.DataFrame(rows)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(df)} entries to {OUTPUT_CSV}")
    print(df["category"].value_counts())
    if "rt60_sec" in df.columns:
        print("\nRT60 stats (real + simulated RIRs only):")
        print(df[df["rt60_sec"].notna()]["rt60_sec"].describe())

    return df


if __name__ == "__main__":
    curate_rir_dataset()