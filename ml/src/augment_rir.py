import os
import numpy as np
import librosa
import scipy.signal

def augment_with_rir(audio_y, sr, rir_y, rir_sr):
    """
    Convolves a dry audio signal with a Room Impulse Response (RIR).
    This applies the acoustic signature of the RIR to the audio.
    """
    # Resample RIR to match audio sr if necessary
    if sr != rir_sr:
        rir_y = librosa.resample(rir_y, orig_sr=rir_sr, target_sr=sr)
    
    # Trim the RIR to remove any leading silence for accurate convolution
    rir_y, _ = librosa.effects.trim(rir_y, top_db=60)
    
    # Normalize RIR power so it doesn't change overall volume drastically
    rir_y = rir_y / np.max(np.abs(rir_y))
    
    # Perform convolution
    convolved = scipy.signal.convolve(audio_y, rir_y, mode='full')
    
    # Normalize back to avoid clipping
    if np.max(np.abs(convolved)) > 1.0:
        convolved = convolved / np.max(np.abs(convolved))
        
    return convolved

def process_file_with_rir(audio_path, rir_path, output_path=None):
    """
    Loads an audio file and an RIR, convolves them, and optionally saves the result.
    """
    # Load audio
    sr = 16000
    audio_y, _ = librosa.load(audio_path, sr=sr, mono=True)
    
    # Load RIR
    rir_y, rir_sr = librosa.load(rir_path, sr=None, mono=True)
    
    # Convolve
    convolved_audio = augment_with_rir(audio_y, sr, rir_y, rir_sr)
    
    # Save if output path provided
    if output_path:
        import soundfile as sf
        sf.write(output_path, convolved_audio, sr)
        
    return convolved_audio, sr

if __name__ == "__main__":
    # Example usage (will need actual paths)
    print("RIR Augmentation script ready.")
    print("Use `process_file_with_rir(audio_path, rir_path, output_path)` to convolve.")
