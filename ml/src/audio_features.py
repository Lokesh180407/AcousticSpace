import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from pathlib import Path


def extract_features(filepath, sr=16000, n_mels=128, n_mfcc=20):
    """Extract spectrogram + acoustic features from a single audio file."""
    y, sr = librosa.load(str(filepath), sr=sr)

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    log_mel = librosa.power_to_db(mel, ref=np.max)

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    flatness = librosa.feature.spectral_flatness(y=y)
    zcr = librosa.feature.zero_crossing_rate(y=y)

    return {
        "y": y,
        "sr": sr,
        "log_mel": log_mel,
        "mfcc": mfcc,
        "centroid": centroid,
        "rolloff": rolloff,
        "flatness": flatness,
        "zcr": zcr,
    }


def plot_features(features, title="Audio Features", save_path=None):
    """Visualize log-mel spectrogram and MFCC side by side."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 6))

    img1 = librosa.display.specshow(
        features["log_mel"], sr=features["sr"], x_axis="time", y_axis="mel", ax=axes[0]
    )
    axes[0].set_title(f"{title} - Log-Mel Spectrogram")
    fig.colorbar(img1, ax=axes[0], format="%+2.0f dB")

    img2 = librosa.display.specshow(
        features["mfcc"], sr=features["sr"], x_axis="time", ax=axes[1]
    )
    axes[1].set_title(f"{title} - MFCC")
    fig.colorbar(img2, ax=axes[1])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        print(f"Saved plot to {save_path}")
    plt.show()


if __name__ == "__main__":
    # Quick test using a sample audio file
    sample_path = Path("ml/data/raw/sample/test_audio.wav")

    if not sample_path.exists():
        print(f"No sample file found at {sample_path}")
        print("Place any .wav file there to test the pipeline.")
    else:
        features = extract_features(sample_path)
        print("Feature shapes:")
        print(f"  log_mel: {features['log_mel'].shape}")
        print(f"  mfcc: {features['mfcc'].shape}")
        print(f"  centroid: {features['centroid'].shape}")
        print(f"  rolloff: {features['rolloff'].shape}")
        print(f"  flatness: {features['flatness'].shape}")
        print(f"  zcr: {features['zcr'].shape}")

        plot_features(features, title="Test Sample", save_path="ml/data/protocols/sample_features.png")