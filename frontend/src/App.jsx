import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState("");
  const [status, setStatus] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleUpload() {
    setError("");
    setResult(null);
    setStatus("");
    setJobId("");

    if (!file) {
      setError("Pick an audio file first.");
      return;
    }

    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      setError(`Upload failed: ${await res.text()}`);
      return;
    }

    const data = await res.json();
    setJobId(data.job_id);
    setStatus("processing");
  }

  async function pollJob(id) {
    setError("");

    const res = await fetch(`${API_BASE}/jobs/${id}`);
    if (!res.ok) {
      setError(`Poll failed: ${await res.text()}`);
      return;
    }

    const data = await res.json();
    setStatus(data.status);

    if (data.status === "done") setResult(data.result);
    if (data.status === "error") setError(data.error || "Unknown error");
  }

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "system-ui" }}>
      <h1>Classical Performance Diagnostic Tool (v1)</h1>

      <p style={{ marginTop: 8 }}>
        Upload a recording to generate tempo and loudness curves (dummy data for now).
      </p>

      <div style={{ marginTop: 16 }}>
        <input
          type="file"
          accept=".wav,.mp3,.m4a,.flac,.ogg"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button onClick={handleUpload} style={{ marginLeft: 12 }}>
          Upload & Analyze
        </button>
      </div>

      {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}

      {jobId && (
        <div style={{ marginTop: 16 }}>
          <p><b>Job ID:</b> {jobId}</p>
          <p><b>Status:</b> {status}</p>
          <button onClick={() => pollJob(jobId)}>Poll status</button>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <h2>Result JSON</h2>
          <pre style={{ background: "#f6f8fa", padding: 16, overflowX: "auto" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}