# 🔍 AcousticSpace — Full Project Analysis (Week 3)

## Project Overview
**AcousticSpace** — Deepfake Audio Detection via Room Impulse Response (RIR)  
A security tool that detects AI-generated audio by analyzing acoustic fingerprints (room reverb, breathing patterns) rather than vocal biometrics.

---

## 👥 Team Status

| Person | Branch | Role | Status |
|--------|--------|------|--------|
| **Lokesh** | `frontend` | Frontend (React) | ⛔ LEFT — Only scaffolded empty React app |
| **Deshna** | `deshna` | ML / Data Science | ✅ Active — CNN model + data pipeline done |
| **Parth** | `petkar-branch` | Backend (FastAPI) | ✅ Active — Auth + Audio upload API done |

---

## ✅ What Deshna Has Done (ML Branch)

All work lives in `ml/src/`:

| File | What It Does |
|------|-------------|
| `audio_features.py` | Extracts MFCC, spectrogram, spectral features using Librosa |
| `augment_rir.py` | Speech-RIR augmentation (large hall vs small room) |
| `augmentation.py` | Full augmentation pipeline |
| `rir_features.py` | RIR-specific feature extraction |
| `feature_extraction.py` | Combined feature pipeline |
| `curate_asvspoof.py` | ASVspoof dataset curation (287 lines) |
| `dataset_loader.py` | PyTorch Dataset + DataLoader for spoof classification |
| `model.py` | Baseline CNN architecture for spoof detection |
| `train.py` | Training loop for baseline CNN classifier |
| `test_pipeline.py` | Pipeline test runner |
| `ml/data/protocols/` | RIR index (61,260 files), ASV dataset, real speech samples |

**Week 3 task for Deshna**: Fine-tuning HuggingFace Audio Spectrogram Transformer (AST) — likely in progress.

---

## ✅ What Parth Has Done (petkar-branch)

All work lives in `backend/app/`:

| File/Folder | What It Does |
|-------------|-------------|
| `api/v1/auth.py` | Full JWT auth: register, login, refresh token, logout, /me |
| `api/v1/upload.py` | Audio file upload endpoint — validates type/size, saves to disk |
| `api/deps.py` | Auth dependency injection (get_current_user, resolve_owner_identity) |
| `core/security.py` | bcrypt hashing, JWT create/decode, token hashing |
| `core/config.py` | Settings (DB URL, JWT secret, upload limits, allowed audio types) |
| `db/session.py` | SQLAlchemy session + `get_db` dependency |
| `models/user.py` | User model (email, hashed_password, full_name, is_active) |
| `models/audio.py` | UploadedAudio model (supports both auth users + guests) |
| `models/prediction.py` | PredictionResult model (label, confidence_score, raw_output JSON) |
| `models/analysis.py` | AnalysisHistory model |
| `models/refresh_token.py` | RefreshToken model (with revoke support) |
| `models/audit_log.py` | AuditLog model |

**Parth's API endpoints ready:**
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /audio` — Upload audio file

**Missing from Parth's backend**: No ML inference endpoint yet (`POST /audio/{id}/analyze`).

---

## ⛔ What Lokesh Left Behind (frontend branch)

The `frontend/` folder has **only a bare Vite+React scaffold**:
- `index.html` — Empty React root (no content)
- `src/main.tsx` — Presumably default Vite entry
- **Zero components, zero pages, zero API calls**

**This is 100% pending.**

---

## 📋 Week-by-Week Frontend Plan vs Reality

| Week | Frontend Target | Reality |
|------|----------------|---------|
| Week 1 | UI Scaffolding, audio upload component, static dashboard layout | ❌ Nothing done |
| Week 2 | Waveform visualizer (WaveSurfer.js), audio upload handler | ❌ Nothing done |
| Mid-Project | Architecture check, large audio uploads, basic waveform graphs | ❌ Nothing done |
| **Week 3** | **Results UI: confidence scores panel, suspicious segments highlight** | ❌ Nothing done |
| Week 4 | Refine/Polish, state management for analysis history | Pending |

---

## 🎯 Week 3 Action Plan — What YOU Two Should Do

### You (Parth) — Backend

**Priority: Add ML Inference Endpoint** (Week 3 task)

1. **`POST /audio/{audio_id}/analyze`** — triggers the ML model on an uploaded file
   - Load the trained CNN model from `ml/src/model.py`
   - Run `feature_extraction.py` on the uploaded file
   - Return `PredictionResult` (label: real/fake, confidence_score, suspicious_segments)
   - Save result to DB using existing `PredictionResult` model ✅ already defined by you

2. **`GET /audio/{audio_id}/result`** — fetch analysis results
   - Returns `AnalysisHistory` with all `PredictionResult` records

3. **(Optional) Job Queue** — If inference is slow, add a background task with FastAPI's `BackgroundTasks` or Celery.

> These endpoints are the **critical link** the frontend needs to function.

---

### You (Deshna) — Help Frontend + Finish ML

**Priority 1: Frontend (Taking over Lokesh's role)**

Build a React + TypeScript frontend. Use the existing Vite scaffold in `frontend/`.

**Pages to build:**

#### Page 1: Landing / Upload Page
- Hero section explaining AcousticSpace
- Drag-and-drop audio file uploader
- Calls `POST /audio` (Parth's existing endpoint ✅)
- Shows upload progress bar

#### Page 2: Analysis / Results Page
- Shows waveform using **WaveSurfer.js**
- Calls `POST /audio/{id}/analyze` (Parth's new endpoint)
- Displays:
  - 🟢/🔴 Real vs Fake verdict badge
  - Confidence score (e.g. 94.3% Fake)
  - Suspicious timestamp segments highlighted on waveform
  - RIR feature summary (room size, reverb signature)

#### Page 3: History Page (Week 4, but plan now)
- List of past analyses with results
- Uses local state + API calls

**Priority 2: Finish ML (Week 3 target)**
- Fine-tune HuggingFace AST model
- Export model weights for Parth's inference endpoint

---

## 🔗 API Contract (Frontend ↔ Backend)

```
POST   /auth/register          → { email, password, full_name }
POST   /auth/login             → { access_token, refresh_token }
POST   /audio                  → multipart/form-data { file } → { audio.id, ... }
POST   /audio/{id}/analyze     → triggers ML → { label, confidence_score, raw_output }
GET    /audio/{id}/result      → fetch results → { label, confidence, segments }
```

---

## 🗂️ Recommended Tech Stack for Frontend

| Concern | Choice |
|---------|--------|
| Framework | React + TypeScript (Vite — already scaffolded) |
| Styling | Tailwind CSS or Vanilla CSS |
| Waveform | WaveSurfer.js |
| HTTP | Axios or fetch with custom hook |
| State | React Context + useState (simple) |
| Auth | JWT stored in localStorage |

---

## ⚡ Immediate Next Steps (This Week)

1. **Parth**: Build `POST /audio/{id}/analyze` endpoint
2. **Deshna**: Set up React routes (React Router) and start Upload page
3. **Both**: Agree on exact request/response shapes for the analyze endpoint
4. **Deshna**: Wire WaveSurfer.js into the results page

> [!IMPORTANT]
> The ML inference endpoint is the **critical dependency**. Frontend cannot show real results without it. Parth should prioritize this first.

> [!TIP]
> For Week 3 deadline: Focus on Upload page + Results page first. History page can wait for Week 4 polish.
