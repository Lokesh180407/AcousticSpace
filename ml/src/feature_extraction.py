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
    
    # 4. Breathing Cadence Alignment (Replaces Month 1 silence_ratio)
    # Natural speech has regular syllable peaks with characteristic breath pauses.
    # We find peaks in the energy envelope to represent syllables.
    peak_indices, _ = scipy.signal.find_peaks(energy, distance=sr//10, prominence=0.05 * np.max(energy))
    if len(peak_indices) > 1:
        # Calculate intervals between peaks (syllable pacing in seconds)
        intervals = np.diff(peak_indices) / sr
        
        # Deepfakes often have unnaturally consistent or erratic pacing.
        # We calculate the coefficient of variation (CV) of the intervals.
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        cadence_variation = float(std_interval / (mean_interval + 1e-10))
        
        # Identify "breath pauses" as intervals significantly longer than the mean
        breath_pauses = np.sum(intervals > (mean_interval + 1.5 * std_interval))
        breath_rate = float(breath_pauses / (len(y) / sr))
    else:
        cadence_variation = 0.0
        breath_rate = 0.0
    
    return {
        "spectral_decay_rate": float(avg_decay_rate),
        "drr_est_db": float(drr_est),
        "cadence_variation": cadence_variation,
        "breath_rate": breath_rate
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
