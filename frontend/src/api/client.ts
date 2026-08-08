// ─── API Client ──────────────────────────────────────────────────────────────
// Change BASE_URL to match the backend when deployed.
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

// ─── Local history for Week 4 ────────────────────────────────────────────────
export interface HistoryEntry {
  audio_id: string;
  filename: string;
  file_size_bytes: number;
  label: "real" | "fake";
  confidence_score: number;
  analyzed_at: string;
}

const HISTORY_KEY = "acousticspace_history";

export function getHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToHistory(entry: HistoryEntry): void {
  const history = getHistory();
  // Avoid duplicates by audio_id
  const filtered = history.filter((h) => h.audio_id !== entry.audio_id);
  filtered.unshift(entry); // newest first
  // Keep last 50
  localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered.slice(0, 50)));
}

export function clearHistory(): void {
  localStorage.removeItem(HISTORY_KEY);
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

  const res = await fetch(`${BASE_URL}/api/v1/audio`, {
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
 * Calls the real backend endpoint.
 */
export async function analyzeAudio(audioId: string): Promise<AnalysisResult> {
  const res = await fetch(`${BASE_URL}/api/v1/audio/${audioId}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...getGuestHeader(),
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

/**
 * Fetch stored analysis result for an audio ID.
 */
export async function getAnalysisResult(audioId: string): Promise<AnalysisResult> {
  const res = await fetch(`${BASE_URL}/api/v1/audio/${audioId}/result`, {
    headers: {
      ...getAuthHeader(),
      ...getGuestHeader(),
    },
  });

  if (!res.ok) throw new Error("Failed to fetch result");
  return res.json();
}
