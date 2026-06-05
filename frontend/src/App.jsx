import { useState, useRef, useEffect } from "react";

const STAGES = [
  { id: 1, label: "Intent Extraction", icon: "🧠", desc: "Parsing natural language into structured intent" },
  { id: 2, label: "System Design", icon: "🏗️", desc: "Architecting entities, flows, and roles" },
  { id: 3, label: "Schema Generation", icon: "⚙️", desc: "Generating DB, API, UI, and Auth schemas" },
  { id: "validation", label: "Validation & Repair", icon: "🔧", desc: "Detecting and fixing cross-layer issues" },
  { id: 4, label: "Refinement", icon: "✨", desc: "Resolving inconsistencies across all layers" },
];

const EXAMPLE_PROMPTS = [
  "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
  "Create an e-commerce platform with product listings, shopping cart, Stripe checkout, order tracking, and an admin panel.",
  "Build a project management tool like Trello with boards, cards, teams, due dates, and file attachments.",
  "Create a SaaS analytics dashboard with multi-tenant support, charts, data export, team collaboration, and billing.",
];

const API_BASE = import.meta.env.VITE_API_URL;

function StageIndicator({ currentStage, stages, done }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {stages.map((s, i) => {
        const isActive = currentStage === s.id;
        const isDone = done.includes(s.id);
        return (
          <div key={s.id} style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "10px 14px", borderRadius: 10,
            background: isDone ? "rgba(34,197,94,0.08)" : isActive ? "rgba(139,92,246,0.12)" : "rgba(255,255,255,0.02)",
            border: `1px solid ${isDone ? "rgba(34,197,94,0.25)" : isActive ? "rgba(139,92,246,0.4)" : "rgba(255,255,255,0.06)"}`,
            transition: "all 0.3s ease",
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 13, fontWeight: 700,
              background: isDone ? "#22c55e" : isActive ? "#8b5cf6" : "rgba(255,255,255,0.06)",
              color: isDone || isActive ? "white" : "rgba(255,255,255,0.3)",
              flexShrink: 0,
              boxShadow: isActive ? "0 0 12px rgba(139,92,246,0.5)" : "none",
              animation: isActive ? "pulse 1.5s infinite" : "none",
            }}>
              {isDone ? "✓" : isActive ? "●" : i + 1}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: isDone ? "#86efac" : isActive ? "#c4b5fd" : "rgba(255,255,255,0.4)" }}>
                {s.label}
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", marginTop: 1 }}>{s.desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SchemaTab({ label, data, color }) {
  const [open, setOpen] = useState(false);
  const summary = getSchemaSummary(label, data);

  return (
    <div style={{
      borderRadius: 12,
      border: `1px solid ${color}33`,
      background: `${color}08`,
      overflow: "hidden",
      marginBottom: 8,
    }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 16px", cursor: "pointer",
          borderBottom: open ? `1px solid ${color}22` : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 18 }}>{getSchemaIcon(label)}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: color }}>{label}</div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 1 }}>{summary}</div>
          </div>
        </div>
        <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 16 }}>{open ? "▲" : "▼"}</span>
      </div>
      {open && (
        <pre style={{
          margin: 0, padding: "14px 16px",
          fontSize: 11.5, lineHeight: 1.6,
          color: "#e2e8f0", overflowX: "auto",
          maxHeight: 400, overflowY: "auto",
          background: "rgba(0,0,0,0.3)",
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

function getSchemaSummary(label, data) {
  if (!data) return "No data";
  if (label === "Database") return `${data.tables?.length || 0} tables`;
  if (label === "API") return `${data.endpoints?.length || 0} endpoints`;
  if (label === "UI") return `${data.pages?.length || 0} pages`;
  if (label === "Auth") return `${data.roles?.length || 0} roles`;
  if (label === "Business Logic") return `${data.rules?.length || 0} rules`;
  if (label === "Design") return `${data.entities?.length || 0} entities, ${data.flows?.length || 0} flows`;
  if (label === "Intent") return `${data.features?.length || 0} features`;
  return "";
}

function getSchemaIcon(label) {
  const m = { Database: "🗄️", API: "🔌", UI: "🖥️", Auth: "🔐", "Business Logic": "⚡", Design: "📐", Intent: "🧠", Meta: "📊" };
  return m[label] || "📋";
}

function MetricCard({ label, value, sub, color }) {
  return (
    <div style={{
      padding: "14px 16px", borderRadius: 10,
      background: `${color}10`,
      border: `1px solid ${color}30`,
      flex: 1, minWidth: 120,
    }}>
      <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.6)", marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentStage, setCurrentStage] = useState(null);
  const [doneStages, setDoneStages] = useState([]);
  const [streamLog, setStreamLog] = useState([]);
  const [tab, setTab] = useState("output");
  const [evalResult, setEvalResult] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [streamLog]);

  const handleCompile = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setCurrentStage(null);
    setDoneStages([]);
    setStreamLog([]);
    setTab("output");

    try {
      const res = await fetch(`${API_BASE}/compile/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n").filter(l => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const event = JSON.parse(line.slice(6));
            handleStreamEvent(event);
          } catch {}
        }
      }
    } catch (e) {
      setError("Failed to connect to backend. Make sure the server is running on port 8000.");
    } finally {
      setLoading(false);
      setCurrentStage(null);
    }
  };

  const handleStreamEvent = (event) => {
    setStreamLog(prev => [...prev, event]);
    if (event.event === "stage") {
      setCurrentStage(event.stage);
    } else if (event.event === "stage_complete") {
      setDoneStages(prev => [...prev, event.stage]);
    } else if (event.event === "validation_complete") {
      setDoneStages(prev => [...prev, "validation"]);
    } else if (event.event === "complete") {
      setResult(event.data);
      setDoneStages([1, 2, 3, "validation", 4]);
    } else if (event.event === "error") {
      setError(event.message);
    }
  };

  const handleEval = async (type) => {
    setEvalLoading(true);
    setEvalResult(null);
    try {
      const res = await fetch(`${API_BASE}/eval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_type: type }),
      });
      const data = await res.json();
      setEvalResult(data);
    } catch (e) {
      setError("Eval failed: " + e.message);
    } finally {
      setEvalLoading(false);
    }
  };

  const downloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${result.app?.name?.replace(/\s+/g, "_") || "app"}_config.json`;
    a.click();
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      color: "#e2e8f0",
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 4px; }
        textarea:focus, button:focus { outline: none; }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        padding: "16px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "rgba(10,10,20,0.95)", backdropFilter: "blur(10px)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, boxShadow: "0 0 20px rgba(124,58,237,0.4)",
          }}>⚡</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 17, letterSpacing: "-0.02em" }}>App Compiler</div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: -1 }}>
              Natural Language → Executable App Config
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["output", "eval", "logs"].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: "6px 14px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600,
              background: tab === t ? "rgba(139,92,246,0.2)" : "transparent",
              color: tab === t ? "#c4b5fd" : "rgba(255,255,255,0.4)",
              transition: "all 0.2s",
            }}>{t.charAt(0).toUpperCase() + t.slice(1)}</button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 65px)" }}>
        {/* Left Panel */}
        <div style={{
          width: 340, flexShrink: 0,
          borderRight: "1px solid rgba(255,255,255,0.06)",
          padding: 20, overflowY: "auto",
          display: "flex", flexDirection: "column", gap: 16,
        }}>
          {/* Prompt Input */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.4)", marginBottom: 8, letterSpacing: "0.05em" }}>
              APP DESCRIPTION
            </div>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Describe the app you want to build..."
              style={{
                width: "100%", minHeight: 120, padding: "12px 14px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 10, color: "#e2e8f0", fontSize: 13,
                resize: "vertical", lineHeight: 1.6,
                transition: "border-color 0.2s",
              }}
              onFocus={e => e.target.style.borderColor = "rgba(139,92,246,0.5)"}
              onBlur={e => e.target.style.borderColor = "rgba(255,255,255,0.1)"}
            />
          </div>

          {/* Examples */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.3)", marginBottom: 8, letterSpacing: "0.05em" }}>
              EXAMPLES
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {EXAMPLE_PROMPTS.map((p, i) => (
                <button key={i} onClick={() => setPrompt(p)} style={{
                  textAlign: "left", padding: "8px 10px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 8, color: "rgba(255,255,255,0.45)",
                  fontSize: 11.5, cursor: "pointer", lineHeight: 1.4,
                  transition: "all 0.2s",
                }}
                  onMouseEnter={e => { e.target.style.background = "rgba(139,92,246,0.08)"; e.target.style.borderColor = "rgba(139,92,246,0.2)"; e.target.style.color = "rgba(255,255,255,0.7)"; }}
                  onMouseLeave={e => { e.target.style.background = "rgba(255,255,255,0.03)"; e.target.style.borderColor = "rgba(255,255,255,0.06)"; e.target.style.color = "rgba(255,255,255,0.45)"; }}
                >
                  {p.slice(0, 80)}...
                </button>
              ))}
            </div>
          </div>

          {/* Compile Button */}
          <button
            onClick={handleCompile}
            disabled={loading || !prompt.trim()}
            style={{
              width: "100%", padding: "12px 0",
              background: loading ? "rgba(139,92,246,0.3)" : "linear-gradient(135deg, #7c3aed, #4f46e5)",
              border: "none", borderRadius: 10, color: "white",
              fontSize: 14, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
              boxShadow: loading ? "none" : "0 4px 20px rgba(124,58,237,0.35)",
              transition: "all 0.2s", letterSpacing: "0.02em",
            }}
          >
            {loading ? "⚙️  Compiling..." : "⚡  Compile App"}
          </button>

          {/* Stage Pipeline Progress */}
          {(loading || result) && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.3)", marginBottom: 10, letterSpacing: "0.05em" }}>
                PIPELINE STAGES
              </div>
              <StageIndicator currentStage={currentStage} stages={STAGES} done={doneStages} />
            </div>
          )}
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>

          {/* Output Tab */}
          {tab === "output" && (
            <div style={{ animation: "fadeIn 0.3s ease" }}>
              {error && (
                <div style={{
                  padding: "14px 18px", borderRadius: 10,
                  background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
                  color: "#fca5a5", fontSize: 13, marginBottom: 16,
                }}>
                  ❌ {error}
                </div>
              )}

              {!result && !loading && (
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  height: "60vh", color: "rgba(255,255,255,0.2)", textAlign: "center",
                }}>
                  <div style={{ fontSize: 64, marginBottom: 16 }}>⚡</div>
                  <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Ready to Compile</div>
                  <div style={{ fontSize: 13, maxWidth: 320, lineHeight: 1.6 }}>
                    Enter a natural language app description on the left and click Compile.
                  </div>
                </div>
              )}

              {loading && !result && (
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  height: "60vh", gap: 16,
                }}>
                  <div style={{
                    width: 60, height: 60, borderRadius: "50%",
                    border: "3px solid rgba(139,92,246,0.2)",
                    borderTop: "3px solid #8b5cf6",
                    animation: "spin 1s linear infinite",
                  }} />
                  <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
                  <div style={{ fontSize: 14, color: "rgba(255,255,255,0.5)" }}>Pipeline running...</div>
                </div>
              )}

              {result && (
                <div style={{ animation: "fadeIn 0.4s ease" }}>
                  {/* App Header */}
                  <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    marginBottom: 20,
                  }}>
                    <div>
                      <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>
                        {result.app?.name}
                      </div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginTop: 3 }}>
                        {result.app?.description}
                      </div>
                    </div>
                    <button onClick={downloadJSON} style={{
                      padding: "8px 16px", borderRadius: 8,
                      background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)",
                      color: "#86efac", fontSize: 13, fontWeight: 600, cursor: "pointer",
                    }}>
                      ⬇ Download JSON
                    </button>
                  </div>

                  {/* Metrics */}
                  <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
                    <MetricCard label="Tables" value={result.database?.tables?.length || 0} color="#60a5fa" />
                    <MetricCard label="Endpoints" value={result.api?.endpoints?.length || 0} color="#a78bfa" />
                    <MetricCard label="Pages" value={result.ui?.pages?.length || 0} color="#34d399" />
                    <MetricCard label="Roles" value={result.auth?.roles?.length || 0} color="#fb923c" />
                    <MetricCard label="Repairs" value={result.meta?.repairs?.length || 0} color="#f472b6"
                      sub="auto-fixed issues" />
                    <MetricCard label="Latency"
                      value={`${((result.meta?.total_latency_ms || 0) / 1000).toFixed(1)}s`}
                      color="#fbbf24" />
                  </div>

                  {/* Assumptions & Features */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                    {result.app?.features?.length > 0 && (
                      <div style={{ padding: 14, borderRadius: 10, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.3)", marginBottom: 8, letterSpacing: "0.05em" }}>FEATURES</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {result.app.features.map((f, i) => (
                            <span key={i} style={{ padding: "3px 8px", borderRadius: 6, background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.2)", fontSize: 11, color: "#c4b5fd" }}>{f}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {result.app?.assumptions?.length > 0 && (
                      <div style={{ padding: 14, borderRadius: 10, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.3)", marginBottom: 8, letterSpacing: "0.05em" }}>ASSUMPTIONS MADE</div>
                        {result.app.assumptions.slice(0, 4).map((a, i) => (
                          <div key={i} style={{ fontSize: 11.5, color: "rgba(255,255,255,0.45)", marginBottom: 4, lineHeight: 1.4 }}>• {a}</div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Schema Sections */}
                  <div style={{ marginBottom: 10, fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.3)", letterSpacing: "0.05em" }}>
                    GENERATED SCHEMAS
                  </div>
                  <SchemaTab label="Database" data={result.database} color="#60a5fa" />
                  <SchemaTab label="API" data={result.api} color="#a78bfa" />
                  <SchemaTab label="UI" data={result.ui} color="#34d399" />
                  <SchemaTab label="Auth" data={result.auth} color="#fb923c" />
                  <SchemaTab label="Business Logic" data={result.business_logic} color="#f472b6" />
                  <SchemaTab label="Design" data={result.design} color="#fbbf24" />
                  <SchemaTab label="Intent" data={result.intent} color="#38bdf8" />

                  {/* Repairs */}
                  {result.meta?.repairs?.length > 0 && (
                    <div style={{ marginTop: 16, padding: 14, borderRadius: 10, background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.2)" }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: "#fbbf24", marginBottom: 8 }}>🔧 Auto-Repairs Applied ({result.meta.repairs.length})</div>
                      {result.meta.repairs.map((r, i) => (
                        <div key={i} style={{ fontSize: 11.5, color: "rgba(255,255,255,0.45)", marginBottom: 3 }}>• {r}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Eval Tab */}
          {tab === "eval" && (
            <div style={{ animation: "fadeIn 0.3s ease" }}>
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 6 }}>Evaluation Framework</div>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                  Run 10 real prompts + 10 edge cases and measure success rate, latency, and repairs.
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                {["all", "real", "edge"].map(t => (
                  <button key={t} onClick={() => handleEval(t)} disabled={evalLoading} style={{
                    padding: "10px 20px", borderRadius: 8,
                    background: evalLoading ? "rgba(255,255,255,0.05)" : "rgba(139,92,246,0.15)",
                    border: "1px solid rgba(139,92,246,0.3)",
                    color: "#c4b5fd", fontSize: 13, fontWeight: 600, cursor: evalLoading ? "not-allowed" : "pointer",
                  }}>
                    {evalLoading ? "Running..." : `Run ${t === "all" ? "All (20)" : t === "real" ? "Real (10)" : "Edge (10)"}`}
                  </button>
                ))}
              </div>

              {evalLoading && (
                <div style={{ textAlign: "center", padding: 40, color: "rgba(255,255,255,0.3)" }}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>⚙️</div>
                  <div>Running evaluation suite... This may take several minutes.</div>
                </div>
              )}

              {evalResult && !evalLoading && (
                <div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
                    <MetricCard label="Success Rate" value={`${evalResult.summary.success_rate_pct}%`} color="#22c55e" />
                    <MetricCard label="Real Prompts" value={`${evalResult.summary.real_success_rate_pct}%`} color="#60a5fa" sub="success rate" />
                    <MetricCard label="Edge Cases" value={`${evalResult.summary.edge_success_rate_pct}%`} color="#f59e0b" sub="success rate" />
                    <MetricCard label="Avg Latency" value={`${(evalResult.summary.avg_latency_ms / 1000).toFixed(1)}s`} color="#a78bfa" />
                    <MetricCard label="Avg Repairs" value={evalResult.summary.avg_repairs_per_run} color="#f472b6" sub="per run" />
                    <MetricCard label="Est. Cost" value={`$${evalResult.summary.total_cost_usd_estimate || "—"}`} color="#fbbf24" />
                  </div>

                  <div style={{ borderRadius: 10, overflow: "hidden", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", padding: "10px 14px", background: "rgba(255,255,255,0.04)", fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.4)", letterSpacing: "0.05em" }}>
                      <div>PROMPT</div><div>STATUS</div><div>LATENCY</div><div>REPAIRS</div><div>TABLES/EP/PAGES</div>
                    </div>
                    {evalResult.results?.map((r, i) => (
                      <div key={i} style={{
                        display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr",
                        padding: "10px 14px", borderTop: "1px solid rgba(255,255,255,0.04)",
                        fontSize: 12, alignItems: "center",
                        background: i % 2 ? "rgba(255,255,255,0.01)" : "transparent",
                      }}>
                        <div style={{ color: "rgba(255,255,255,0.6)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={r.prompt}>
                          <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, marginRight: 6, background: r.label.startsWith("real") ? "rgba(96,165,250,0.15)" : "rgba(251,191,36,0.15)", color: r.label.startsWith("real") ? "#93c5fd" : "#fcd34d" }}>
                            {r.label}
                          </span>
                          {r.prompt}
                        </div>
                        <div style={{ color: r.success ? "#22c55e" : "#ef4444", fontWeight: 700 }}>
                          {r.success ? "✓ Pass" : `✗ ${r.failure_type || "fail"}`}
                        </div>
                        <div style={{ color: "rgba(255,255,255,0.5)" }}>{(r.latency_ms / 1000).toFixed(1)}s</div>
                        <div style={{ color: r.repairs_count > 0 ? "#fbbf24" : "rgba(255,255,255,0.3)" }}>{r.repairs_count}</div>
                        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11 }}>
                          {r.output_summary ? `${r.output_summary.tables}/${r.output_summary.endpoints}/${r.output_summary.pages}` : "—"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Logs Tab */}
          {tab === "logs" && (
            <div style={{ animation: "fadeIn 0.3s ease" }}>
              <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 16 }}>Pipeline Logs</div>
              <div
                ref={logRef}
                style={{
                  background: "rgba(0,0,0,0.4)", borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.06)",
                  padding: 16, height: "calc(100vh - 180px)", overflowY: "auto",
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
                }}
              >
                {streamLog.length === 0 ? (
                  <div style={{ color: "rgba(255,255,255,0.2)" }}>No logs yet. Run a compilation to see the pipeline events.</div>
                ) : (
                  streamLog.map((e, i) => (
                    <div key={i} style={{ marginBottom: 6, padding: "4px 8px", borderRadius: 4, background: getLogBg(e.event) }}>
                      <span style={{ color: getLogColor(e.event), fontWeight: 700 }}>[{e.event}]</span>{" "}
                      <span style={{ color: "rgba(255,255,255,0.55)" }}>
                        {e.message || (e.stage ? `Stage ${e.stage}` : "") || (e.repairs ? `${e.repairs.length} repairs` : "") || ""}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getLogColor(event) {
  const m = { start: "#60a5fa", stage: "#a78bfa", stage_complete: "#22c55e", validation_complete: "#fbbf24", complete: "#34d399", error: "#ef4444" };
  return m[event] || "rgba(255,255,255,0.4)";
}
function getLogBg(event) {
  if (event === "error") return "rgba(239,68,68,0.08)";
  if (event === "complete") return "rgba(52,211,153,0.05)";
  if (event === "stage_complete") return "rgba(34,197,94,0.05)";
  return "transparent";
}
