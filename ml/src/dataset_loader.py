import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import soundfile as sf
import pandas as pd
from pathlib import Path
import os
import imageio_ffmpeg

os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())


def _create_mel_filterbank(sr, n_fft, n_mels):
    """Create a mel filterbank matrix (equivalent to librosa.filters.mel)."""
    # Mel scale conversion helpers
    def hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel):
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    fmin, fmax = 0.0, sr / 2.0
    mel_min = hz_to_mel(fmin)
    mel_max = hz_to_mel(fmax)

    # n_mels + 2 points linearly spaced in mel scale
    mels = np.linspace(mel_min, mel_max, n_mels + 2)
    freqs = mel_to_hz(mels)

    # FFT bin frequencies
    fft_freqs = np.linspace(0, sr / 2.0, n_fft // 2 + 1)

    # Build the filterbank
    filterbank = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        lower = freqs[i]
        center = freqs[i + 1]
        upper = freqs[i + 2]

        for j, f in enumerate(fft_freqs):
            if lower <= f <= center and center != lower:
                filterbank[i, j] = (f - lower) / (center - lower)
            elif center < f <= upper and upper != center:
                filterbank[i, j] = (upper - f) / (upper - center)

    return filterbank


class SpoofDataset(Dataset):
    """
    PyTorch Dataset for bonafide/spoof audio classification.
    Expects a CSV with columns: filepath, label (bonafide/spoof)
    Converts each audio file into a log-mel spectrogram tensor on the fly.

    Uses soundfile for audio I/O and pure PyTorch for mel spectrogram
    computation. This avoids both librosa (blocked by numba/AppControl)
    and torchaudio.load (broken torchcodec default backend).
    """

    MAX_RETRIES = 5

    def __init__(self, csv_path, sr=16000, n_mels=128, fixed_frames=605,
                 n_fft=2048, hop_length=512):
        self.df = pd.read_csv(csv_path)
        self.sr = sr
        self.n_mels = n_mels
        self.fixed_frames = fixed_frames
        self.n_fft = n_fft
        self.hop_length = hop_length

        # Map string labels to integers: bonafide=0, spoof=1
        self.label_map = {"bonafide": 0, "spoof": 1}

        # Pre-build mel filterbank as a torch tensor (reused for every sample)
        mel_fb = _create_mel_filterbank(sr, n_fft, n_mels)
        self.mel_fb = torch.tensor(mel_fb, dtype=torch.float32)

        # Pre-build Hann window for STFT
        self.window = torch.hann_window(n_fft)

    def __len__(self):
        return len(self.df)

    def _load_log_mel(self, filepath):
        # Load audio with soundfile (no numba, no torchcodec)
        data, orig_sr = sf.read(str(filepath), dtype="float32")

        # Convert to mono if stereo
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Resample if needed (simple linear interpolation)
        if orig_sr != self.sr:
            target_len = int(len(data) * self.sr / orig_sr)
            waveform = torch.tensor(data, dtype=torch.float32).unsqueeze(0)
            waveform = F.interpolate(
                waveform.unsqueeze(0), size=target_len, mode="linear",
                align_corners=False
            ).squeeze(0).squeeze(0)
        else:
            waveform = torch.tensor(data, dtype=torch.float32)

        # Compute STFT
        stft = torch.stft(
            waveform, n_fft=self.n_fft, hop_length=self.hop_length,
            window=self.window, return_complex=True
        )
        power_spec = stft.abs() ** 2  # (n_fft//2 + 1, time)

        # Apply mel filterbank
        mel = self.mel_fb @ power_spec  # (n_mels, time)

        # Convert to log scale (same as librosa.power_to_db with ref=np.max)
        mel = torch.clamp(mel, min=1e-10)
        log_mel = 10.0 * torch.log10(mel)
        log_mel = log_mel - log_mel.max()  # normalize to 0 dB reference
        log_mel = torch.clamp(log_mel, min=-80.0)  # top_db=80

        # Pad or crop time axis so every sample has the same shape
        if log_mel.shape[1] < self.fixed_frames:
            pad_width = self.fixed_frames - log_mel.shape[1]
            log_mel = F.pad(log_mel, (0, pad_width))
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