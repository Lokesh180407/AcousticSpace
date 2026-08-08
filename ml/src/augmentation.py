import numpy as np
import librosa
import soundfile as sf
from scipy.signal import fftconvolve
from pathlib import Path
import pandas as pd


def apply_rir(clean_audio, rir_audio):
    """Convolve clean speech with a room impulse response."""
    reverbed = fftconvolve(clean_audio, rir_audio)[:len(clean_audio)]
    # Normalize to avoid clipping
    max_val = np.max(np.abs(reverbed))
    if max_val > 0:
        reverbed = reverbed / max_val * 0.95
    return reverbed


def augment_speech_with_rir(speech_path, rir_path, output_path, sr=16000):
    speech, _ = librosa.load(str(speech_path), sr=sr)
    rir, _ = librosa.load(str(rir_path), sr=sr)

    reverbed_speech = apply_rir(speech, rir)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), reverbed_speech, sr)

    print(f"Saved augmented audio to {output_path}")
    print(f"  Original duration: {len(speech)/sr:.2f}s")
    print(f"  RIR duration: {len(rir)/sr:.2f}s")
    print(f"  Output duration: {len(reverbed_speech)/sr:.2f}s")


if __name__ == "__main__":
    speech_path = Path("ml/data/raw/sample/real_speech.wav")
    rir_index = pd.read_csv("ml/data/protocols/rir_index.csv")

    # --- Existing: real RIR (large hall) — already done, kept as is ---
    real_rirs = rir_index[rir_index["category"] == "real_rir"]
    if len(real_rirs) > 0:
        chosen_rir = real_rirs.iloc[0]["filepath"]
        print(f"[Large room/hall] Using RIR: {chosen_rir}")
        augment_speech_with_rir(
            speech_path=speech_path,
            rir_path=chosen_rir,
            output_path="ml/data/protocols/real_speech_in_room.wav",
        )

    print()

    # --- New: small room, from simulated RIRs ---
    small_room_rirs = rir_index[
        (rir_index["category"] == "simulated_rir") &
        (rir_index["filepath"].str.contains("smallroom", case=False, na=False))
    ]
    if len(small_room_rirs) > 0:
        chosen_small_rir = small_room_rirs.iloc[0]["filepath"]
        print(f"[Small room] Using RIR: {chosen_small_rir}")
        augment_speech_with_rir(
            speech_path=speech_path,
            rir_path=chosen_small_rir,
            output_path="ml/data/protocols/real_speech_in_smallroom.wav",
        )
    else:
        print("No small room RIRs found — check subfolder naming in rir_index.csv")