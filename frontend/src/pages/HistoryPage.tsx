import { useState, useEffect } from "react";
import { getHistory, clearHistory, type HistoryEntry } from "../api/client";
import "./HistoryPage.css";

interface HistoryPageProps {
  onNavigateToUpload: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HistoryPage({ onNavigateToUpload }: HistoryPageProps) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const handleClear = () => {
    clearHistory();
    setHistory([]);
  };

  return (
    <div className="history-page">
      {/* Header */}
      <div className="history-header">
        <div className="history-header-left">
          <div className="header-brand">
            <div className="header-brand-dot" />
            AcousticSpace
          </div>
        </div>
        <div className="history-header-right">
          <button className="nav-btn active" id="history-tab-btn">History</button>
          <button className="nav-btn" id="upload-tab-btn" onClick={onNavigateToUpload}>Upload</button>
        </div>
      </div>

      {/* Title */}
      <div className="history-title-section">
        <h1 className="history-title">Analysis History</h1>
        <p className="history-subtitle">Your recent deepfake detection results, stored locally on this device.</p>
        {history.length > 0 && (
          <button className="clear-btn" id="clear-history-btn" onClick={handleClear}>
            🗑 Clear History
          </button>
        )}
      </div>

      {/* Table or Empty State */}
      {history.length === 0 ? (
        <div className="history-empty">
          <div className="empty-icon">📭</div>
          <div className="empty-title">No analyses yet</div>
          <div className="empty-desc">Upload an audio file to see your analysis history here.</div>
          <button className="empty-action" onClick={onNavigateToUpload}>Upload Audio</button>
        </div>
      ) : (
        <div className="history-table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Size</th>
                <th>Verdict</th>
                <th>Confidence</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => {
                const isFake = entry.label === "fake";
                const confidence = Math.round(entry.confidence_score * 100);
                return (
                  <tr key={entry.audio_id}>
                    <td className="cell-filename">
                      <span className="file-icon">🎵</span>
                      {entry.filename}
                    </td>
                    <td className="cell-size">{formatFileSize(entry.file_size_bytes)}</td>
                    <td>
                      <span className={`verdict-pill ${isFake ? "pill-fake" : "pill-real"}`}>
                        {isFake ? "🚨 Fake" : "✅ Real"}
                      </span>
                    </td>
                    <td>
                      <div className="confidence-cell">
                        <div className="confidence-bar-bg">
                          <div
                            className={`confidence-bar-fill ${isFake ? "fill-fake" : "fill-real"}`}
                            style={{ width: `${confidence}%` }}
                          />
                        </div>
                        <span className="confidence-text">{confidence}%</span>
                      </div>
                    </td>
                    <td className="cell-date">{formatDate(entry.analyzed_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
