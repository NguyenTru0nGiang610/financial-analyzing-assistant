import React, { useState } from "react";

export default function Message({ msg }) {
  const isUser = msg.role === "user";
  const [openSources, setOpenSources] = useState(false);

  return (
    <div className={`message ${msg.role}`}>
      {!isUser && <div className="avatar">◆</div>}
      <div className="message-body">
        <div className={`bubble ${msg.isError ? "error" : ""}`}>
          {isUser ? (
            <p>{msg.text}</p>
          ) : (
            <div
              className="markdown"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
            />
          )}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="citations">
            <button
              className="citations-toggle"
              onClick={() => setOpenSources((v) => !v)}
            >
              {openSources ? "▾" : "▸"} {msg.sources.length} citation
              {msg.sources.length > 1 ? "s" : ""}
            </button>

            {openSources && (
              <ol className="citation-list">
                {msg.sources.map((s, i) => (
                  <li key={i} className="citation">
                    <div className="citation-head">
                      <span className="citation-num">{i + 1}</span>
                      <span className="citation-source">
                        {shortName(s.source)}
                        {s.page != null && ` · p.${s.page}`}
                      </span>
                    </div>
                    {s.text && <p className="citation-text">{snippet(s.text)}</p>}
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function shortName(path) {
  if (!path) return "source";
  return String(path).split(/[/\\]/).pop();
}

function snippet(text, n = 240) {
  const t = String(text).trim().replace(/\s+/g, " ");
  return t.length > n ? `${t.slice(0, n)}…` : t;
}

// Minimal, dependency-free Markdown → HTML for assistant answers.
function renderMarkdown(src) {
  if (!src) return "";
  const esc = (s) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  const inline = (s) =>
    esc(s)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");

  const lines = src.split("\n");
  let html = "";
  let inList = false;

  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      closeList();
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);

    if (heading) {
      closeList();
      const level = heading[1].length;
      html += `<h${level}>${inline(heading[2])}</h${level}>`;
    } else if (bullet) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${inline(bullet[1])}</li>`;
    } else {
      closeList();
      html += `<p>${inline(line)}</p>`;
    }
  }
  closeList();
  return html;
}
