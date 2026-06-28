const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.error) detail = body.error;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function createSession() {
  const res = await fetch(`${BASE_URL}/session`);
  return handle(res);
}

export async function uploadFile(file, sessionId) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/upload?session_id=${sessionId}`, {
    method: "POST",
    body: formData,
  });

  return handle(res);
}

export async function queryRAG(sessionId, query, pipeline = "langchain") {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, query, pipeline }),
  });

  return handle(res);
}
