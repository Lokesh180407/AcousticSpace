from feature_extraction import process_audio_file
import json

audio_path = '../data/protocols/real_speech_in_room.wav'
print(f"Testing feature extraction on: {audio_path}")

try:
    res = process_audio_file(audio_path)
    print(f"AST Mel Spec shape: {res['mel_spectrogram'].shape}")
    print(f"Acoustic space features: {json.dumps(res['acoustic_features'], indent=2)}")
    print("Feature extraction pipeline ran successfully!")
except Exception as e:
    print(f"Error during feature extraction: {e}")
