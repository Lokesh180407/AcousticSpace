# 🎵 AcousticSpace: Deepfake Detection via Room Impulse Response (RIR)

AcousticSpace is an advanced deepfake audio detection platform built for real-world security analysis. Unlike standard biometric detectors that analyze only vocal inflections, AcousticSpace isolates the **Room Impulse Response (RIR)** signature—analyzing how sound reverberates off background acoustic environments—to flag artificially generated voice clips.

---

## ✨ Key Features & Modules

- 🔊 **Audio Feature Extraction Pipeline (`librosa`)**: Extracts log-mel spectrograms, MFCCs, spectral centroid, spectral flatness, and zero-crossing rate. Isolates acoustic room reflections and $RT_{60}$ decay characteristics.
- 🧠 **PyTorch Deep Learning Classifier (`AudioSpoofCNN`)**: Custom 2D Convolutional Neural Network with adaptive global average pooling trained on spectrogram features to detect spatial acoustic inconsistencies.
- ⚡ **FastAPI Backend Gateway**: Low-latency REST API providing audio upload handling, session management, and ML inference routing.
- 📊 **Interactive Analyst Dashboard (React + TypeScript + Vite)**:
  - Drag-and-drop audio uploader (supporting WAV, MP3, OGG, FLAC, M4A).
  - Waveform visualizer powered by `Wavesurfer.js` with real-time playback.
  - Dynamic confidence verdict ring and acoustic anomaly score breakdown.
  - Analysis history tracking.
- 🐳 **Containerized Deployment**: Multi-stage Docker and Docker Compose environment.

---

## 🛠️ Tech Stack

- **Machine Learning & Audio**: Python 3.10+, PyTorch, Librosa, Torchaudio, Scikit-Learn, Pandas, NumPy
- **Backend API**: FastAPI, SQLAlchemy, SQLite/PostgreSQL, Uvicorn, Pydantic
- **Frontend Dashboard**: React 18, TypeScript, Vite, Wavesurfer.js, Vanilla CSS
- **DevOps**: Docker, Docker Compose

---

## 🚀 Quick Start Guide

### Option A: Running with Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/Lokesh180407/AcousticSpace.git
   cd AcousticSpace
