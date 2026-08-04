import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import "./ResultsPage.css";
import type { UploadResponse, AnalysisResult } from "../api/client";

interface ResultsPageProps {
  file: File;
  uploadResponse: UploadResponse;
  result: AnalysisResult;
  onReset: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function ResultsPage({ file, uploadResponse, result, onReset }: ResultsPageProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  // Use React state — not DOM refs — to drive button UI
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const prediction = result.prediction;
  const isFake = prediction?.label === "fake";
  const confidence = prediction ? Math.round(prediction.confidence_score * 100) : 0;
  const rawOutput = prediction?.raw_output as Record<string, number> | null;

  useEffect(() => {
    if (!waveformRef.current) return;

    // Reset state when a new file is loaded
    setIsReady(false);
    setIsPlaying(false);

    const ws = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: isFake ? "#ef4444" : "#22c55e",
      progressColor: isFake ? "#dc2626" : "#16a34a",
      cursorColor: "#6366f1",
      cursorWidth: 1,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 80,
      normalize: true,
    });

    ws.loadBlob(file);
    wavesurferRef.current = ws;

    ws.on("ready", () => setIsReady(true));
    ws.on("play",  () => setIsPlaying(true));
    ws.on("pause", () => setIsPlaying(false));
    ws.on("finish",() => setIsPlaying(false));

    return () => {
      ws.destroy();
      wavesurferRef.current = null;
    };
  }, [file, isFake]);

  const togglePlay = () => {
    if (wavesurferRef.current && isReady) {
      wavesurferRef.current.playPause();
    }
  };

  return (
    <div className="results-page">
      {/* Header */}
      <div className="results-header">
        <button id="back-btn" className="back-btn" onClick={onReset}>
          ← Analyze Another File
        </button>
        <div className="header-brand">
          <div className="header-brand-dot" />
          AcousticSpace
        </div>
      </div>

      {/* Verdict Banner */}
      <div className={`verdict-banner ${isFake ? "verdict-fake" : "verdict-real"}`}>
        <div className="verdict-icon">{isFake ? "🚨" : "✅"}</div>
        <div className="verdict-content">
          <div className="verdict-label">{isFake ? "DEEPFAKE DETECTED" : "AUTHENTIC AUDIO"}</div>
          <div className="verdict-description">
            {isFake
              ? "This audio shows strong signs of AI generation based on RIR mismatch and spectral anomalies."
              : "This audio matches expected acoustic properties of a real recording environment."}
          </div>
        </div>
        <div className="verdict-confidence">
          <div className="confidence-ring">
            <svg viewBox="0 0 36 36" className="ring-svg">
              <path
                className="ring-bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="ring-fill"
                strokeDasharray={`${confidence}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                style={{ stroke: isFake ? "#ef4444" : "#22c55e" }}
              />
            </svg>
            <div className="ring-label">
              <span className="ring-pct">{confidence}%</span>
              <span className="ring-sub">confidence</span>
            </div>
          </div>
        </div>
      </div>

      {/* Waveform Section */}
      <div className="section waveform-section">
        <div className="section-title">🎵 Audio Waveform</div>
        <div className="waveform-card">
          <div className="file-info">
            <span className="file-name">📁 {uploadResponse.audio.original_filename}</span>
            <span className="file-size">{formatFileSize(uploadResponse.audio.file_size_bytes)}</span>
          </div>
          <div id="waveform-container" ref={waveformRef} className="waveform-container" />
          <div className="waveform-controls">
            <button
              id="play-pause-btn"
              className="play-btn"
              onClick={togglePlay}
              disabled={!isReady}
            >
              {!isReady ? "⏳ Loading..." : isPlaying ? "⏸ Pause" : "▶ Play"}
            </button>
            {isReady && (
              <span className="waveform-hint">Click waveform to seek</span>
            )}
          </div>
        </div>
      </div>

      {/* Feature Scores */}
      {rawOutput && (
        <div className="section">
          <div className="section-title">📊 Acoustic Feature Scores</div>
          <div className="feature-scores">
            {Object.entries(rawOutput).map(([key, value]) => {
              const pct = Math.round((value as number) * 100);
              const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
              const danger = pct > 70;
              const warn = pct > 40 && pct <= 70;
              return (
                <div key={key} className="score-row">
                  <div className="score-label">{label}</div>
                  <div className="score-bar-wrap">
                    <div
                      className={`score-bar-fill ${danger ? "danger" : warn ? "warn" : "safe"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className={`score-pct ${danger ? "danger" : warn ? "warn" : "safe"}`}>{pct}%</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Model Info */}
      <div className="section model-info-section">
        <div className="section-title">🤖 Model Info</div>
        <div className="model-info-grid">
          <div className="info-card">
            <div className="info-label">Model</div>
            <div className="info-value">{prediction?.model_name ?? "—"}</div>
          </div>
          <div className="info-card">
            <div className="info-label">Version</div>
            <div className="info-value">{prediction?.model_version ?? "—"}</div>
          </div>
          <div className="info-card">
            <div className="info-label">File ID</div>
            <div className="info-value mono">{uploadResponse.audio.id.slice(0, 8)}…</div>
          </div>
          <div className="info-card">
            <div className="info-label">Status</div>
            <div className="info-value">{result.status}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
