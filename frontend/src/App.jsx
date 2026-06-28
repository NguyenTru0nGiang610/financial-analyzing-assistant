import React, { useEffect, useState } from "react";
import { createSession } from "./api";
import SourcesPanel from "./components/SourcesPanel";
import Chat from "./components/Chat";
import StudioPanel from "./components/StudioPanel";

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);

  // Documents that have been uploaded + indexed for this session.
  const [sources, setSources] = useState([]);
  // A question the Studio panel asked the chat to run.
  const [pendingQuestion, setPendingQuestion] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await createSession();
        setSessionId(data.session_id);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  const addSource = (source) =>
    setSources((prev) => [...prev, { id: crypto.randomUUID(), ...source }]);

  if (error) {
    return (
      <div className="boot-screen">
        <div className="boot-card error">
          <h2>Can&apos;t reach the assistant</h2>
          <p>{error}</p>
          <p className="muted">
            Make sure the API is running on <code>localhost:8000</code>.
          </p>
        </div>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="boot-screen">
        <div className="boot-card">
          <div className="spinner" />
          <p>Starting your notebook…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <span className="brand-name">FinNotebook</span>
          <span className="brand-sub">Financial Analyzing Assistant</span>
        </div>
        <div className="topbar-right">
          <span className="session-pill" title={sessionId}>
            session · {sessionId.slice(0, 8)}
          </span>
        </div>
      </header>

      <main className="workspace">
        <SourcesPanel
          sessionId={sessionId}
          sources={sources}
          onSourceAdded={addSource}
        />
        <Chat
          sessionId={sessionId}
          hasSources={sources.length > 0}
          pendingQuestion={pendingQuestion}
          onConsumeQuestion={() => setPendingQuestion(null)}
        />
        <StudioPanel
          hasSources={sources.length > 0}
          onAskQuestion={(q) => setPendingQuestion(q)}
        />
      </main>
    </div>
  );
}
