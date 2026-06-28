import React, { useEffect, useRef, useState } from "react";
import { queryRAG } from "../api";
import Message from "./Message";

export default function Chat({
  sessionId,
  hasSources,
  pendingQuestion,
  onConsumeQuestion,
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      const res = await queryRAG(sessionId, q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `⚠️ ${err.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Run a question forwarded from the Studio panel.
  useEffect(() => {
    if (pendingQuestion) {
      send(pendingQuestion);
      onConsumeQuestion?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingQuestion]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <section className="panel chat-panel">
      <div className="panel-head">
        <h2>Chat</h2>
      </div>

      <div className="messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <h1>Ask your financial documents anything</h1>
            <p className="muted">
              FinNotebook answers using only the sources you upload, with
              citations back to the exact page.
            </p>
          </div>
        ) : (
          messages.map((m, i) => <Message key={i} msg={m} />)
        )}

        {loading && (
          <div className="message assistant">
            <div className="avatar">◆</div>
            <div className="bubble typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            hasSources
              ? "Ask about revenue, margins, risks…"
              : "Upload a source to start chatting"
          }
        />
        <button
          className="send-btn"
          onClick={() => send()}
          disabled={loading || !input.trim()}
          title="Send"
        >
          ➤
        </button>
      </div>
      {!hasSources && (
        <div className="composer-hint muted">
          Tip: add a PDF in the Sources panel — answers are grounded in your
          uploads.
        </div>
      )}
    </section>
  );
}
