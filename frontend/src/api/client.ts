// ─── API Client ──────────────────────────────────────────────────────────────
// Change BASE_URL to match Parth's backend when deployed.
// Default: FastAPI runs on http://localhost:8000
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────
export interface UploadedAudio {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  status: "uploaded" | "queued" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface UploadResponse {
  audio: UploadedAudio;
  guest_id: string | null;
}

export interface PredictionResult {
  id: string;
  label: "real" | "fake";
  confidence_score: number; // 0.0 - 1.0
  model_name: string;
  model_version: string;
  raw_output: Record<string, unknown> | null;
}

export interface AnalysisResult {
  audio_id: string;
  status: "completed" | "processing" | "failed";
  prediction: PredictionResult | null;
  error?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function getGuestHeader(): Record<string, string> {
  const guestId = localStorage.getItem("guest_id");
  return guestId ? { "X-Guest-Id": guestId } : {};
}

// ─── API Calls ───────────────────────────────────────────────────────────────

/**
 * Upload an audio file to the backend.
 * Works for both authenticated users and anonymous guests.
 */
export async function uploadAudio(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/audio`, {
    method: "POST",
    headers: {
      ...getAuthHeader(),
      ...getGuestHeader(),
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }

  // Save guest_id from response header so future requests can track this session
  const guestId = res.headers.get("X-Guest-Id");
  if (guestId) localStorage.setItem("guest_id", guestId);

  return res.json();
}

/**
 * Trigger ML analysis on an uploaded audio file.
 * NOTE: This endpoint will be built by Parth in Week 3.
 * For now returns a mock response if backend is not ready.
 */
export async function analyzeAudio(audioId: string): Promise<AnalysisResult> {
  try {
    const res = await fetch(`${BASE_URL}/audio/${audioId}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
        ...getGuestHeader(),
      },
    });

    if (!res.ok) throw new Error("Analysis endpoint not ready yet");
    return res.json();
  } catch {
    // ── MOCK response until Parth builds the endpoint ──────────────────────
    console.warn("⚠️ Using mock ML result — backend analyze endpoint not ready yet.");
    await new Promise((r) => setTimeout(r, 2500)); // simulate processing
    const isFake = Math.random() > 0.45;
    return {
      audio_id: audioId,
      status: "completed",
      prediction: {
        id: crypto.randomUUID(),
        label: isFake ? "fake" : "real",
        confidence_score: isFake
          ? 0.72 + Math.random() * 0.25
          : 0.55 + Math.random() * 0.3,
        model_name: "AcousticSpace-CNN-v1",
        model_version: "0.1.0",
        raw_output: {
          rir_score: 0.83,
          breathing_alignment: 0.41,
          spectral_anomaly: 0.76,
        },
      },
    };
    // ── End mock ───────────────────────────────────────────────────────────
  }
}

/**
 * Fetch stored analysis result for an audio ID.
 */
export async function getAnalysisResult(audioId: string): Promise<AnalysisResult> {
  const res = await fetch(`${BASE_URL}/audio/${audioId}/result`, {
    headers: {
      ...getAuthHeader(),
      ...getGuestHeader(),
    },
  });

  if (!res.ok) throw new Error("Failed to fetch result");
  return res.json();
}
