import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import librosa
import pandas as pd
from pathlib import Path


class SpoofDataset(Dataset):
    """
    PyTorch Dataset for bonafide/spoof audio classification.
    Expects a CSV with columns: filepath, label (bonafide/spoof)
    Converts each audio file into a log-mel spectrogram tensor on the fly.
    """

    def __init__(self, csv_path, sr=16000, n_mels=128, fixed_frames=605):
        self.df = pd.read_csv(csv_path)
        self.sr = sr
        self.n_mels = n_mels
        self.fixed_frames = fixed_frames  # pad/crop so all samples match model input shape

        # Map string labels to integers: bonafide=0, spoof=1
        self.label_map = {"bonafide": 0, "spoof": 1}

    def __len__(self):
        return len(self.df)

    def _load_log_mel(self, filepath):
        y, sr = librosa.load(str(filepath), sr=self.sr)
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
        log_mel = librosa.power_to_db(mel, ref=np.max)

        # Pad or crop time axis so every sample has the same shape
        if log_mel.shape[1] < self.fixed_frames:
            pad_width = self.fixed_frames - log_mel.shape[1]
            log_mel = np.pad(log_mel, ((0, 0), (0, pad_width)), mode="constant")
        else:
            log_mel = log_mel[:, :self.fixed_frames]

        return log_mel

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        filepath = row["filepath"]
        label_str = row["label"]

        log_mel = self._load_log_mel(filepath)

        # Shape: (1, n_mels, fixed_frames) — matches model's expected input
        features = torch.tensor(log_mel, dtype=torch.float32).unsqueeze(0)
        label = torch.tensor(self.label_map[label_str], dtype=torch.long)

        return features, label


def build_dummy_csv_for_testing(output_path):
    """
    Creates a small placeholder CSV using your existing demo audio files,
    with FAKE labels — purely to test the Dataset/DataLoader mechanics
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
    dummy_csv_path = "ml/data/protocols/dummy_test_index.csv"
    build_dummy_csv_for_testing(dummy_csv_path)

    dataset = SpoofDataset(dummy_csv_path)
    print(f"\nDataset size: {len(dataset)}")

    # Test loading a single sample
    features, label = dataset[0]
    print(f"Sample 0 - features shape: {features.shape}, label: {label}")

    # Test DataLoader batching
    loader = DataLoader(dataset, batch_size=2, shuffle=True)
    for batch_features, batch_labels in loader:
        print(f"\nBatch features shape: {batch_features.shape}")
        print(f"Batch labels: {batch_labels}")