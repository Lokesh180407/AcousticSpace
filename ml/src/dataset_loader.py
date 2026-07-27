import torch
import torchaudio
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from pathlib import Path
import os
import imageio_ffmpeg

os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())


class SpoofDataset(Dataset):
    """
    PyTorch Dataset for bonafide/spoof audio classification.
    Expects a CSV with columns: filepath, label (bonafide/spoof)
    Converts each audio file into a log-mel spectrogram tensor on the fly.

    Fixed vs. the original version:
      - No more unbounded recursion on load failure (was recursing on every
        bad file with no depth cap -> guaranteed RecursionError once enough
        failures happen in a row).
      - The real exception is now printed, not swallowed, so failures are
        actually diagnosable.
      - Retries are capped (MAX_RETRIES) and iterative. If every retry fails,
        we raise loudly instead of returning silently-wrong data -- a model
        that trains "successfully" on garbage/zero tensors is worse than a
        loud crash, because it produces misleading results.
      - Uses torchaudio instead of librosa to avoid numba dependency.
    """

    MAX_RETRIES = 5

    def __init__(self, csv_path, sr=16000, n_mels=128, fixed_frames=605):
        self.df = pd.read_csv(csv_path)
        self.sr = sr
        self.n_mels = n_mels
        self.fixed_frames = fixed_frames  # pad/crop so all samples match model input shape

        # Map string labels to integers: bonafide=0, spoof=1
        self.label_map = {"bonafide": 0, "spoof": 1}

        # Pre-build the mel spectrogram transform (reused for every sample)
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=sr,
            n_mels=n_mels,
            n_fft=2048,
            hop_length=512,
        )
        self.amp_to_db = torchaudio.transforms.AmplitudeToDB(top_db=80)

    def __len__(self):
        return len(self.df)

    def _load_log_mel(self, filepath):
        waveform, orig_sr = torchaudio.load(str(filepath))

        # Resample if needed
        if orig_sr != self.sr:
            resampler = torchaudio.transforms.Resample(orig_sr, self.sr)
            waveform = resampler(waveform)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Compute log-mel spectrogram
        mel = self.mel_transform(waveform)        # (1, n_mels, time)
        log_mel = self.amp_to_db(mel).squeeze(0)   # (n_mels, time)

        # Pad or crop time axis so every sample has the same shape
        if log_mel.shape[1] < self.fixed_frames:
            pad_width = self.fixed_frames - log_mel.shape[1]
            log_mel = torch.nn.functional.pad(log_mel, (0, pad_width))
        else:
            log_mel = log_mel[:, :self.fixed_frames]

        return log_mel.numpy()

    def __getitem__(self, idx):
        import random

        tried = set()
        current_idx = idx

        for attempt in range(self.MAX_RETRIES):
            row = self.df.iloc[current_idx]
            filepath = row["filepath"]
            label_str = row["label"]

            try:
                log_mel = self._load_log_mel(filepath)
                features = torch.tensor(log_mel, dtype=torch.float32).unsqueeze(0)
                label = torch.tensor(self.label_map[label_str], dtype=torch.long)
                return features, label

            except Exception as e:
                # Print the REAL error -- this is the whole point of the fix.
                print(
                    f"[WARNING] Failed to load {filepath} "
                    f"(attempt {attempt + 1}/{self.MAX_RETRIES}): "
                    f"{type(e).__name__}: {e}"
                )
                tried.add(current_idx)
                # Pick a new index we haven't already tried this call.
                remaining = self.MAX_RETRIES - attempt - 1
                if remaining <= 0:
                    break
                current_idx = random.randint(0, len(self.df) - 1)
                while current_idx in tried and len(tried) < len(self.df):
                    current_idx = random.randint(0, len(self.df) - 1)

        raise RuntimeError(
            f"Gave up after {self.MAX_RETRIES} attempts starting from idx {idx}. "
            f"Tried indices: {tried}. This usually means a large fraction of your "
            f"dataset split is unreadable -- run check_dataset_integrity.py before "
            f"training further."
        )


def build_dummy_csv_for_testing(output_path):
    """
    Creates a small placeholder CSV using your existing demo audio files,
    with FAKE labels -- purely to test the Dataset/DataLoader mechanics
    before real ASVspoof data is ready.
    """
    rows = [
        {"filepath": "ml/data/raw/sample/real_speech.wav", "label": "bonafide"},
        {"filepath": "ml/data/protocols/real_speech_in_room.wav", "label": "spoof"},
        {"filepath": "ml/data/protocols/real_speech_in_smallroom.wav", "label": "bonafide"},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Dummy test CSV saved to {output_path}")
    return df


if __name__ == "__main__":
    real_csv_path = "ml/data/protocols/asvspoof2021_la_index.csv"

    dataset = SpoofDataset(real_csv_path)
    print(f"\nDataset size: {len(dataset)}")

    # Test loading a single sample
    features, label = dataset[0]
    print(f"Sample 0 - features shape: {features.shape}, label: {label}")

    # Test DataLoader batching
    loader = DataLoader(dataset, batch_size=2, shuffle=True)
    for batch_features, batch_labels in loader:
        print(f"\nBatch features shape: {batch_features.shape}")
        print(f"Batch labels: {batch_labels}")