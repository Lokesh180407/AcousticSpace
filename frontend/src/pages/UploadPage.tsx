import React, { useCallback, useRef, useState } from "react";
import "./UploadPage.css";
import {
  uploadAudio,
  analyzeAudio,
  addToHistory,
  type UploadResponse,
  type AnalysisResult,
} from "../api/client";
import ResultsPage from "./ResultsPage";

type UploadState = "idle" | "dragging" | "uploading" | "analyzing" | "done" | "error";

interface UploadPageProps {
  onNavigateToHistory?: () => void;
}

const ACCEPTED_TYPES = ["audio/wav", "audio/mpeg", "audio/ogg", "audio/flac", "audio/mp4", "audio/x-m4a"];
const MAX_SIZE_MB = 50;

export default function UploadPage({ onNavigateToHistory }: UploadPageProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);

    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(wav|mp3|ogg|flac|m4a)$/i)) {
      setError("Unsupported format. Please upload a WAV, MP3, OGG, FLAC or M4A file.");
      setState("error");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB}MB.`);
      setState("error");
      return;
    }

    setSelectedFile(file);
    setState("uploading");

    let prog = 0;
    const interval = setInterval(() => {
      prog += Math.random() * 22;
      if (prog >= 90) { clearInterval(interval); prog = 90; }
      setProgress(Math.min(prog, 90));
    }, 100);

    try {
      // Upload audio to real backend
      const uploadRes = await uploadAudio(file);

      clearInterval(interval);
      setProgress(100);
      setUploadResponse(uploadRes);

      setState("analyzing");
      setProgress(0);

      // Run ML analysis via backend
      const analysisRes = await analyzeAudio(uploadRes.audio.id);
      setAnalysisResult(analysisRes);

      // Save to local history for Week 4
      if (analysisRes.prediction) {
        addToHistory({
          audio_id: uploadRes.audio.id,
          filename: file.name,
          file_size_bytes: file.size,
          label: analysisRes.prediction.label,
          confidence_score: analysisRes.prediction.confidence_score,
          analyzed_at: new Date().toISOString(),
        });
      }

      setState("done");
    } catch (err) {
      clearInterval(interval);
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setState("error");
    }
  }, []);

  const onDragEnter = (e: React.DragEvent) => { e.preventDefault(); setState("dragging"); };
  const onDragLeave = (e: React.DragEvent) => { e.preventDefault(); if (state !== "error") setState("idle"); };
  const onDragOver  = (e: React.DragEvent) => { e.preventDefault(); };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setState("idle");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const reset = () => {
    setState("idle");
    setProgress(0);
    setError(null);
    setSelectedFile(null);
    setUploadResponse(null);
    setAnalysisResult(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  if (state === "done" && analysisResult && uploadResponse && selectedFile) {
    return (
      <ResultsPage
        file={selectedFile}
        uploadResponse={uploadResponse}
        result={analysisResult}
        onReset={reset}
      />
    );
  }

  const isProcessing = state === "uploading" || state === "analyzing";

  return (
    <div className="upload-page">
      {/* Topbar */}
      <div className="topbar">
        <div className="topbar-brand">
          <div className="topbar-brand-dot" />
          AcousticSpace
        </div>
        <div className="topbar-right">
          <div className="topbar-badge">Deepfake Detection</div>
          {onNavigateToHistory && (
            <button className="topbar-history-btn" id="history-nav-btn" onClick={onNavigateToHistory}>
              📋 History
            </button>
          )}
        </div>
      </div>

      {/* Hero */}
      <div className="hero">
        <h1 className="hero-title">
          Detect <span className="accent">AI Audio</span> by{" "}
          <br />Room Acoustics
        </h1>
        <p className="hero-subtitle">
          Upload any audio file. We analyze the <strong>Room Impulse Response</strong> signature
          to detect whether it was AI-generated — not just the voice, but how the space sounds.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="upload-container">
        {!isProcessing ? (
          <div
            id="upload-dropzone"
            className={`dropzone ${state === "dragging" ? "dragging" : ""} ${state === "error" ? "error-state" : ""}`}
            onDragEnter={onDragEnter}
            onDragLeave={onDragLeave}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload audio file"
            onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              id="audio-file-input"
              accept=".wav,.mp3,.ogg,.flac,.m4a,audio/*"
              onChange={onFileChange}
              style={{ display: "none" }}
            />
            <div className="dropzone-icon">
              {state === "dragging" ? "📂" : state === "error" ? "⚠️" : "🎵"}
            </div>
            <div className="dropzone-title">
              {state === "dragging" ? "Release to upload" : "Drop your audio file here"}
            </div>
            <div className="dropzone-subtitle">
              or <span className="dropzone-link">click to browse files</span>
            </div>
            <div className="dropzone-formats">WAV · MP3 · OGG · FLAC · M4A &nbsp;·&nbsp; Max {MAX_SIZE_MB}MB</div>
            {error && <div className="dropzone-error">⚠️ {error}</div>}
          </div>
        ) : (
          <div className="progress-card">
            <div className="progress-icon">
              {state === "uploading" ? "⬆️" : "🧠"}
            </div>
            <div className="progress-filename">{selectedFile?.name}</div>
            <div className="progress-label">
              {state === "uploading" ? "Uploading your file..." : "Running deepfake analysis..."}
            </div>

            {state === "uploading" && (
              <div className="progress-bar-wrap">
                <div className="progress-bar" style={{ width: `${progress}%` }} />
              </div>
            )}

            {state === "analyzing" && (
              <div className="analyzing-steps">
                <div className="step active"><div className="step-dot" /> Extracting acoustic features</div>
                <div className="step active"><div className="step-dot" /> Computing RIR signature</div>
                <div className="step active"><div className="step-dot" /> Running CNN classifier</div>
                <div className="step pulse"><div className="step-dot" /> Generating confidence scores...</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feature Cards */}
      <div className="features">
        <div className="feature-card">
          <div className="feature-icon-wrap">🏛️</div>
          <div className="feature-title">Room Impulse Response</div>
          <div className="feature-desc">Analyzes how sound bounces off walls to detect environmental mismatches in AI audio</div>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrap">🌬️</div>
          <div className="feature-title">Breathing Patterns</div>
          <div className="feature-desc">Checks alignment between vocal cadence and natural human breathing rhythms</div>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrap">📊</div>
          <div className="feature-title">Spectrogram Analysis</div>
          <div className="feature-desc">CNN model detects subtle spectral anomalies invisible to the human ear</div>
        </div>
      </div>
    </div>
  );
}
