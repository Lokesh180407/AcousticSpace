import os
import numpy as np
import librosa
import scipy.signal

def light_normalize(y, sr):
    """
    Applies light normalization WITHOUT denoising to preserve RIR tails.
    - DC offset removal
    - RMS normalization
    - Trim leading/trailing silence
    """
    # Remove DC offset
    y = y - np.mean(y)
    
    # RMS normalization
    rms = np.sqrt(np.mean(y**2))
    if rms > 0:
        y = y / rms
        
    # Trim silence (lightly)
    y_trimmed, _ = librosa.effects.trim(y, top_db=60)
    return y_trimmed

def extract_voice_features(y, sr, n_mels=128):
    """
    Branch A: Extracts features for the AST model (raw mel-spectrogram).
    """
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    S_dB = librosa.power_to_db(S, ref=np.max)
    return S_dB

def estimate_blind_acoustic_parameters(y, sr):
    """
    Branch B: Extracts blind statistical estimators of acoustic-space features.
    These are approximations (since true RIR extraction requires a known excitation).
    """
    # 1. Envelope extraction
    envelope = np.abs(scipy.signal.hilbert(y))
    # Provide an odd window length for savgol_filter
    win_len = sr // 100
    if win_len % 2 == 0:
        win_len += 1
    envelope_smooth = scipy.signal.savgol_filter(envelope, window_length=win_len, polyorder=2)
    
    # 2. Heuristic RT60-like decay estimation (Spectral Decay Rate)
    energy = envelope_smooth ** 2
    peaks, _ = scipy.signal.find_peaks(energy, distance=sr//2)
    decays = []
    for p in peaks:
        window = energy[p:min(p + sr//5, len(energy))]
        if len(window) > 10:
            slope = np.polyfit(np.arange(len(window)), np.log10(window + 1e-10), 1)[0]
            decays.append(slope)
    avg_decay_rate = np.mean(decays) if decays else 0.0
    
    # 3. DRR (Direct-to-Reverberant Ratio) Estimate
    direct_energy = np.mean(energy[energy > np.percentile(energy, 95)])
    reverb_energy = np.mean(energy[energy < np.percentile(energy, 50)])
    drr_est = 10 * np.log10((direct_energy + 1e-10) / (reverb_energy + 1e-10))
    
    # 4. Silence/Pause Stats (replaces breathing-cadence for Month 1)
    silence_threshold = 0.1 * np.max(energy)
    silence_ratio = np.sum(energy < silence_threshold) / len(energy)
    
    return {
        "spectral_decay_rate": float(avg_decay_rate),
        "drr_est_db": float(drr_est),
        "silence_ratio": float(silence_ratio)
    }

def process_audio_array(y, sr):
    """
    Main pipeline function that processes an audio array through both branches.
    """
    y_norm = light_normalize(y, sr)
    mel_spec = extract_voice_features(y_norm, sr)
    acoustic_features = estimate_blind_acoustic_parameters(y_norm, sr)
    
    return {
        "mel_spectrogram": mel_spec,
        "acoustic_features": acoustic_features
    }

def process_audio_file(filepath):
    """
    Main pipeline function that processes an audio file through both branches.
    """
    sr = 16000
    y, _ = librosa.load(filepath, sr=sr, mono=True)
    return process_audio_array(y, sr)

if __name__ == "__main__":
    print("Testing feature extraction pipeline on white noise...")
    sr = 16000
    dummy_audio = np.random.randn(sr * 3) # 3 seconds of noise
    results = process_audio_array(dummy_audio, sr)
    print("Acoustic Features extracted:", results["acoustic_features"])
