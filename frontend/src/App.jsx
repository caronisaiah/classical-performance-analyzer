import { useMemo, useState } from "react";
import "./App.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

function formatNum(x, digits = 2) {
  if (x === null || x === undefined) return "—";
  if (!Number.isFinite(x)) return "—";
  return Number(x).toFixed(digits);
}

function InsightCard({ it }) {
  const sev = it?.severity ?? "warn";
  return (
    <div className={`insightCard ${sev}`}>
      <div className="insightTitle">{it?.title ?? "Insight"}</div>
      <div className="insightDetail">{it?.detail ?? ""}</div>
      {it?.suggestion ? (
        <div className="insightSuggestion">
          <span className="insightHint">Try:</span> {it.suggestion}
        </div>
      ) : null}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("compare"); // "compare" | "analyze"
  const [studentFile, setStudentFile] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null);
  const [singleFile, setSingleFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [compareResult, setCompareResult] = useState(null);
  const [analyzeResult, setAnalyzeResult] = useState(null);

  async function handleCompare(e) {
    e?.preventDefault();
    setError("");
    setCompareResult(null);

    if (!studentFile || !referenceFile) {
      setError("Pick both a student file and a reference file.");
      return;
    }

    const form = new FormData();
    form.append("student_file", studentFile);
    form.append("reference_file", referenceFile);

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setCompareResult(data);
    } catch (err) {
      setError(err?.message ?? String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze(e) {
    e?.preventDefault();
    setError("");
    setAnalyzeResult(null);

    if (!singleFile) {
      setError("Pick a file to analyze.");
      return;
    }

    const form = new FormData();
    form.append("file", singleFile);

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setAnalyzeResult(data);
    } catch (err) {
      setError(err?.message ?? String(err));
    } finally {
      setLoading(false);
    }
  }

  // Robust: prefer compareResult.comparison, fallback to top-level copied fields
  const comp = compareResult?.comparison ?? compareResult ?? null;

  const overlapSec = comp?.overlap_sec ?? null;
  const meanAbsBpm = comp?.tempo?.mean_abs_bpm_diff ?? null;
  const meanAbsDb = comp?.loudness?.mean_abs_db_diff ?? null;

  const curves = comp?.curves ?? {};
  const tArr = curves.t ?? curves.student_t ?? [];
  const tempoDiffArr = curves.tempo_diff ?? [];
  const loudDiffArr = curves.loudness_diff_db ?? [];

  const insights = comp?.insights ?? compareResult?.insights ?? [];

  const tempoChart = useMemo(() => {
    const n = Math.min(tArr.length, tempoDiffArr.length);
    return Array.from({ length: n }, (_, i) => ({
      t: tArr[i],
      value: Number.isFinite(tempoDiffArr[i]) ? tempoDiffArr[i] : null,
    }));
  }, [tArr, tempoDiffArr]);

  const loudChart = useMemo(() => {
    const n = Math.min(tArr.length, loudDiffArr.length);
    return Array.from({ length: n }, (_, i) => ({
      t: tArr[i],
      value: Number.isFinite(loudDiffArr[i]) ? loudDiffArr[i] : null,
    }));
  }, [tArr, loudDiffArr]);

  const hasTempoChart = tempoChart.length > 1;
  const hasLoudChart = loudChart.length > 1;

  return (
    <div className="page">
      <div className="topbar">
        <div>
          <div className="title">Classical Performance Analyzer</div>
          <div className="subtitle">
            Upload recordings to compute tempo + loudness curves, and compare
            student vs reference.
          </div>
        </div>

        <div className="segmented">
          <button
            className={`segmentedBtn ${tab === "compare" ? "active" : ""}`}
            onClick={() => {
              setTab("compare");
              setError("");
            }}
            type="button"
          >
            Compare (2 files)
          </button>
          <button
            className={`segmentedBtn ${tab === "analyze" ? "active" : ""}`}
            onClick={() => {
              setTab("analyze");
              setError("");
            }}
            type="button"
          >
            Analyze (1 file)
          </button>
        </div>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      {tab === "compare" ? (
        <div className="card">
          <div className="cardTitle">Compare</div>
          <div className="cardSub">
            Sends <code>student_file</code> and <code>reference_file</code> to{" "}
            <code>POST /compare</code>.
          </div>

          <form className="grid2" onSubmit={handleCompare}>
            <div>
              <div className="label">Student recording</div>
              <input
                className="fileInput"
                type="file"
                accept="audio/*"
                onChange={(e) => setStudentFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div>
              <div className="label">Reference recording</div>
              <input
                className="fileInput"
                type="file"
                accept="audio/*"
                onChange={(e) => setReferenceFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div className="actions">
              <button className="btn" disabled={loading} type="submit">
                {loading ? "Comparing..." : "Compare"}
              </button>
              <button
                className="btn secondary"
                type="button"
                onClick={() => {
                  setStudentFile(null);
                  setReferenceFile(null);
                  setCompareResult(null);
                  setError("");
                }}
              >
                Clear
              </button>
            </div>
          </form>

          {compareResult ? (
            <>
              <div className="divider" />

              <div className="summaryGrid">
                <div className="metric">
                  <div className="metricLabel">Overlap (sec)</div>
                  <div className="metricValue">{formatNum(overlapSec, 2)}</div>
                </div>
                <div className="metric">
                  <div className="metricLabel">Mean |Δ BPM|</div>
                  <div className="metricValue">{formatNum(meanAbsBpm, 2)}</div>
                </div>
                <div className="metric">
                  <div className="metricLabel">Mean |Δ dB|</div>
                  <div className="metricValue">{formatNum(meanAbsDb, 2)}</div>
                </div>
              </div>

              <div className="chartCard">
                <div className="chartTitle">
                  Tempo difference (student − reference)
                </div>

                {hasTempoChart ? (
                  <div className="chartWrap">
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={tempoChart}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="t"
                          tickFormatter={(v) => `${Math.round(v)}s`}
                        />
                        <YAxis />
                        <Tooltip
                          formatter={(v) => [formatNum(v, 2), "Δ BPM"]}
                          labelFormatter={(t) => `t = ${formatNum(t, 2)}s`}
                        />
                        <Line
                          type="monotone"
                          dataKey="value"
                          dot={false}
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="emptyState">
                    No tempo curve data returned (or arrays are empty).
                  </div>
                )}
              </div>

              <div className="chartCard">
                <div className="chartTitle">
                  Loudness difference (student − reference)
                </div>

                {hasLoudChart ? (
                  <div className="chartWrap">
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={loudChart}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="t"
                          tickFormatter={(v) => `${Math.round(v)}s`}
                        />
                        <YAxis />
                        <Tooltip
                          formatter={(v) => [formatNum(v, 2), "Δ dB"]}
                          labelFormatter={(t) => `t = ${formatNum(t, 2)}s`}
                        />
                        <Line
                          type="monotone"
                          dataKey="value"
                          dot={false}
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="emptyState">
                    No loudness curve data returned (or arrays are empty).
                  </div>
                )}
              </div>

              <div className="chartCard">
                <div className="chartTitle">Insights</div>
                {Array.isArray(insights) && insights.length ? (
                  <div className="insightsGrid">
                    {insights.map((it, idx) => (
                      <InsightCard key={idx} it={it} />
                    ))}
                  </div>
                ) : (
                  <div className="emptyState">
                    No insights returned yet. (Check backend: comp.insights)
                  </div>
                )}
              </div>

              <details className="details">
                <summary>Raw compare JSON</summary>
                <pre className="json">
                  {JSON.stringify(compareResult, null, 2)}
                </pre>
              </details>

              <div className="footerHint">Local API: {API_BASE}</div>
            </>
          ) : null}
        </div>
      ) : (
        <div className="card">
          <div className="cardTitle">Analyze</div>
          <div className="cardSub">
            Sends <code>file</code> to <code>POST /upload</code>.
          </div>

          <form className="grid1" onSubmit={handleAnalyze}>
            <div>
              <div className="label">Audio file</div>
              <input
                className="fileInput"
                type="file"
                accept="audio/*"
                onChange={(e) => setSingleFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div className="actions">
              <button className="btn" disabled={loading} type="submit">
                {loading ? "Analyzing..." : "Analyze"}
              </button>
              <button
                className="btn secondary"
                type="button"
                onClick={() => {
                  setSingleFile(null);
                  setAnalyzeResult(null);
                  setError("");
                }}
              >
                Clear
              </button>
            </div>
          </form>

          {analyzeResult ? (
            <>
              <div className="divider" />
              <details className="details">
                <summary>Raw analyze JSON</summary>
                <pre className="json">
                  {JSON.stringify(analyzeResult, null, 2)}
                </pre>
              </details>
              <div className="footerHint">Local API: {API_BASE}</div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
