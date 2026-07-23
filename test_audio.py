import pandas as pd
import librosa
import soundfile as sf
import sys
import os
import torchaudio

def test_audio(csv_path):
    df = pd.read_csv(csv_path)
    if df.empty:
        print("CSV is empty.")
        return
        
    print(f"Testing the first file from {csv_path}:")
    row = df.iloc[0]
    filepath = row["filepath"]
    print(f"Filepath: {filepath}")
    
    if not os.path.exists(filepath):
        print("File does not exist!")
        return

    # Test 1: soundfile directly
    print("\n--- Test 1: soundfile ---")
    try:
        data, samplerate = sf.read(filepath)
        print(f"Success! Shape: {data.shape}, Sample rate: {samplerate}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test 2: torchaudio
    print("\n--- Test 2: torchaudio ---")
    try:
        waveform, sample_rate = torchaudio.load(filepath)
        print(f"Success! Shape: {waveform.shape}, Sample rate: {sample_rate}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test 3: librosa
    print("\n--- Test 3: librosa ---")
    try:
        y, sr = librosa.load(filepath, sr=None)
        print(f"Success! Shape: {y.shape}, Sample rate: {sr}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_audio('ml/data/protocols/asvspoof2021_la_index.csv')
