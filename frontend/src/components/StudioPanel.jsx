import React from "react";

const SUGGESTIONS = [
  "Summarize the key financial highlights.",
  "What was total revenue and how did it change year over year?",
  "Break down operating expenses and margins.",
  "What are the main risk factors mentioned?",
  "Summarize cash flow from operations.",
  "What guidance or outlook does management give?",
];

export default function StudioPanel({ hasSources, onAskQuestion }) {
  return (
    <aside className="panel studio-panel">
      <div className="panel-head">
        <h2>Studio</h2>
      </div>

      <div className="studio-card">
        <h3>Suggested questions</h3>
        <p className="muted">
          One-click prompts tuned for financial reports. They run against your
          uploaded sources.
        </p>
        <div className="suggestions">
          {SUGGESTIONS.map((q) => (
            <button
              key={q}
              className="suggestion"
              disabled={!hasSources}
              onClick={() => onAskQuestion(q)}
            >
              {q}
            </button>
          ))}
        </div>
        {!hasSources && (
          <p className="muted lock-note">Add a source to enable these.</p>
        )}
      </div>

      <div className="studio-card">
        <h3>How it works</h3>
        <ol className="how-list">
          <li>Upload a financial PDF as a source.</li>
          <li>It&apos;s parsed, chunked, embedded &amp; indexed.</li>
          <li>Ask a question — answers are retrieved + cited.</li>
        </ol>
      </div>
    </aside>
  );
}
