import React, { useRef, useState } from "react";
import { uploadFile } from "../api";

export default function SourcesPanel({ sessionId, sources, onSourceAdded }) {
  const inputRef = useRef(null);
  const [status, setStatus] = useState(null); // {type, text}
  const [busy, setBusy] = useState(false);

  const pickFile = () => inputRef.current?.click();

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-uploading the same file
    if (!file) return;

    setBusy(true);
    setStatus({ type: "info", text: `Indexing “${file.name}”…` });

    try {
      await uploadFile(file, sessionId);
      onSourceAdded({
        name: file.name,
        size: file.size,
        addedAt: Date.now(),
      });
      setStatus({ type: "ok", text: `Added “${file.name}”` });
    } catch (err) {
      setStatus({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="panel sources-panel">
      <div className="panel-head">
        <h2>Sources</h2>
        <button
          className="icon-btn"
          onClick={pickFile}
          disabled={busy}
          title="Add a source"
        >
          +
        </button>
      </div>

      <button className="add-source-btn" onClick={pickFile} disabled={busy}>
        {busy ? "Indexing…" : "＋ Add source"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        hidden
        onChange={handleUpload}
      />

      {status && <div className={`status ${status.type}`}>{status.text}</div>}

      <div className="source-list">
        {sources.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📄</div>
            <p>Saved sources will appear here.</p>
            <p className="muted">
              Upload a PDF financial report (10-K, earnings, statements) to
              start asking questions grounded in it.
            </p>
          </div>
        ) : (
          sources.map((s) => (
            <div className="source-item" key={s.id}>
              <span className="source-icon">📑</span>
              <div className="source-meta">
                <div className="source-name" title={s.name}>
                  {s.name}
                </div>
                <div className="source-sub">{formatSize(s.size)}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
