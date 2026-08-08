import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, 'ml/src')

import torch
from backend.app.services.inference import predict, _get_model, _ensure_mel_assets
from ml.src.dataset_loader import SpoofDataset
import numpy as np

# Initialize dataset just to use its _load_log_mel
ds = SpoofDataset('ml/data/protocols/dummy_test_index.csv') # assuming it exists or fails gracefully

# Audio file
audio_path = 'ml/data/protocols/real_speech_in_smallroom.wav'

# Dataset logic
log_mel_np = ds._load_log_mel(audio_path)
dataset_tensor = torch.tensor(log_mel_np, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

# Inference logic
from backend.app.services.inference import SR, N_MELS, N_FFT, HOP_LENGTH, FIXED_FRAMES
import soundfile as sf
import torch.nn.functional as F

mel_fb, window = _ensure_mel_assets()
data, orig_sr = sf.read(audio_path, dtype="float32")
if data.ndim > 1: data = data.mean(axis=1)
waveform = torch.tensor(data, dtype=torch.float32)
if orig_sr != SR:
    target_len = int(len(data) * SR / orig_sr)
    waveform = F.interpolate(
        waveform.unsqueeze(0).unsqueeze(0), size=target_len,
        mode="linear", align_corners=False
    ).squeeze(0).squeeze(0)

stft = torch.stft(waveform, n_fft=N_FFT, hop_length=HOP_LENGTH, window=window, return_complex=True)
power_spec = stft.abs() ** 2
mel = mel_fb @ power_spec
mel = torch.clamp(mel, min=1e-10)
log_mel = 10.0 * torch.log10(mel)
log_mel = log_mel - log_mel.max()
log_mel = torch.clamp(log_mel, min=-80.0)

if log_mel.shape[1] < FIXED_FRAMES:
    pad_width = FIXED_FRAMES - log_mel.shape[1]
    log_mel = F.pad(log_mel, (0, pad_width))
else:
    log_mel = log_mel[:, :FIXED_FRAMES]
inference_tensor = log_mel.unsqueeze(0).unsqueeze(0)

print(f"Dataset tensor shape: {dataset_tensor.shape}")
print(f"Inference tensor shape: {inference_tensor.shape}")

diff = torch.abs(dataset_tensor - inference_tensor).max().item()
print(f"Max difference between tensors: {diff}")

# Run both through model
model = _get_model()
with torch.no_grad():
    ds_logits = model(dataset_tensor)
    inf_logits = model(inference_tensor)
    
print(f"Dataset logits: {ds_logits}")
print(f"Inference logits: {inf_logits}")
