import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ShieldCheck,
  ArrowUpRight,
  ArrowRight,
  Play,
  Square,
  Settings,
  Check,
  LockKeyhole,
  ScanEye,
  Activity,
  FlaskConical,
  FileCheck2,
  ChevronRight,
  Globe,
  ShoppingBag,
  KeyRound,
  MessageSquare,
  Video,
  Code2,
  Download,
  X,
  Eye,
  EyeOff,
  LoaderCircle,
  AlertTriangle,
  Fingerprint,
  Layers,
} from "lucide-react";
import "./style.css";

type Obj = Record<string, any>;
let token = "";
function explainError(message: string) {
  if (message.includes("HTTP 402"))
    return "Gemini requires billing or prepaid credits for this project. Check Google AI Studio → Billing. Your key is saved locally.";
  if (message.includes("HTTP 503"))
    return "Gemini is temporarily unavailable. The task stopped safely; try again later or select another supported model.";
  if (message.includes("HTTP 429"))
    return "Gemini’s rate or quota limit was reached. Wait or check the project’s quota before retrying.";
  if (message.includes("HTTP 401") || message.includes("HTTP 403"))
    return "Gemini rejected access. Check the key’s API permissions and project access in Google AI Studio.";
  return message;
}
async function api(path: string, body?: unknown) {
  const request = () =>
    fetch("/api/" + path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "content-type": "application/json",
        "x-privacy-session": token,
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  let r = await request();
  if (r.status === 401 && path !== "bootstrap") {
    const b = await fetch("/api/bootstrap");
    token = (await b.json()).token;
    r = await request();
  }
  const d = await r.json();
  if (!r.ok)
    throw new Error(
      typeof d.detail === "string" ? d.detail : "Request rejected",
    );
  return d;
}
const profiles = [
  ["checkout", "Checkout", ShoppingBag],
  ["authentication", "Authentication", KeyRound],
  ["support", "Customer support", MessageSquare],
  ["conference", "Conference", Video],
  ["developer", "Developer settings", Code2],
  ["wikipedia", "Wikipedia", Globe],
  ["saucedemo", "SauceDemo", ShoppingBag],
] as const;
function App() {
  const [state, setState] = useState<Obj>({
      detectors: {},
      initializing: true,
    }),
    [tab, setTab] = useState("workspace"),
    [scenario, setScenario] = useState("checkout"),
    [provider, setProvider] = useState("demo"),
    [mode, setMode] = useState("contract"),
    [task, setTask] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [settings, setSettings] = useState(false),
    [key, setKey] = useState(""),
    [model, setModel] = useState("gemini-3.5-flash-lite"),
    [visibleBrowser, setVisibleBrowser] = useState(false),
    [raw, setRaw] = useState(false),
    [attack, setAttack] = useState<Obj | null>(null),
    [report, setReport] = useState<Obj | null>(null),
    [secretRef, setSecretRef] = useState("password"),
    [secretValue, setSecretValue] = useState("");
  useEffect(() => {
    let live = true;
    async function refresh() {
      try {
        if (!token) {
          const b = await api("bootstrap");
          token = b.token;
        }
        const d = await api("status");
        if (live) {
          setState(d);
          if (d.evaluation) setReport(d.evaluation);
        }
      } catch (e) {
        if (live) setError(String(e));
      }
    }
    refresh();
    const id = setInterval(refresh, 1200);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);
  const run = state.run,
    preview = run?.preview,
    active = ["starting", "running", "awaiting_approval"].includes(run?.status),
    ready =
      state.detectors.presidio && state.detectors.ocr && !state.initializing;
  useEffect(() => {
    if (run) {
      setScenario(run.scenario);
      setProvider(run.provider);
      setMode(run.mode);
      setTask("");
      setError("");
    }
  }, [run?.id]);
  useEffect(() => {
    if (run?.status === "blocked" && run?.error)
      setError(explainError(run.error));
  }, [run?.status, run?.error]);
  useEffect(() => {
    if (state.gemini_model) setModel(state.gemini_model);
    if (state.headless !== undefined) setVisibleBrowser(!state.headless);
  }, [state.gemini_model, state.headless]);
  useEffect(() => {
    if (run?.approval)
      setTimeout(
        () =>
          document
            .querySelector(".approval")
            ?.scrollIntoView({ behavior: "smooth", block: "center" }),
        100,
      );
  }, [run?.approval?.id]);
  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const receiptCount =
    run?.receipts?.filter((r: Obj) => r.decision === "allowed").length || 0;
  async function download() {
    const d = await api("export");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([JSON.stringify(d, null, 2)], { type: "application/json" }),
    );
    link.download = "privacylens-evidence.json";
    link.click();
    URL.revokeObjectURL(link.href);
  }
  return (
    <div className="app">
      <aside className="sidebar">
        <a className="brand" href="/">
          <span className="brandmark">
            <ScanEye size={25} />
          </span>
          privacy<span>lens</span>
          <sup>LAB</sup>
        </a>
        <div className="workspace-label">
          LOCAL WORKSPACE <span>01</span>
        </div>
        <nav>
          {[
            ["workspace", "Agent workspace", Layers],
            ["contract", "Privacy contract", Fingerprint],
            ["attacks", "Attack lab", FlaskConical],
            ["evidence", "Evidence & results", FileCheck2],
          ].map(([id, label, Icon]: any) => (
            <button
              key={id}
              className={tab === id ? "selected" : ""}
              onClick={() => setTab(id)}
            >
              <Icon size={19} />
              {label}
              {tab === id && <span className="navdot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <LockKeyhole size={19} />
          <h4>Local by design.</h4>
          <p>
            Sensitive values stay on this machine. Reasoning receives only
            approved context.
          </p>
          <span className="subtle-link" onClick={() => setTab("contract")}>
            Explore the boundary <ArrowUpRight size={14} />
          </span>
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">ES</span>
          <div>
            <strong>Hackathon workspace</strong>
            <small>Private · this device</small>
          </div>
          <button
            className="icon"
            aria-label="Settings"
            onClick={() => setSettings(true)}
          >
            <Settings size={18} />
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace</span>
            <ChevronRight size={14} />
            <span>
              {tab === "workspace"
                ? "Agent studio"
                : tab === "contract"
                  ? "Privacy contract"
                  : tab === "attacks"
                    ? "Attack lab"
                    : "Evidence"}
            </span>
          </div>
          <div>
            <span className={"status-pill " + (ready ? "online" : "")}>
              <i />
              {state.initializing
                ? "Warming up detectors"
                : ready
                  ? "Local protection ready"
                  : "Setup required"}
            </span>
            <button
              className="icon"
              onClick={() => setSettings(true)}
              aria-label="Open settings"
            >
              <Settings size={18} />
            </button>
          </div>
        </header>
        <div className="content">
          {error && (
            <div className="error">
              <AlertTriangle size={18} />
              {error}
              <button className="icon" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {tab === "workspace" && (
            <>
              <div className="page-heading">
                <div className="eyebrow">THE PRIVACY-PRESERVING AGENT</div>
                <h1>
                  Permission to do more.
                  <br />
                  <em>Access to less.</em>
                </h1>
                <p>Give your agent a task. Keep control of what it sees.</p>
                <div className="heading-art">
                  <div className="orbit one" />
                  <div className="orbit two" />
                  <div className="orb">
                    <ShieldCheck size={42} />
                  </div>
                  <span className="art-tag">
                    <LockKeyhole size={12} /> LOCAL PRIVACY BOUNDARY
                  </span>
                </div>
              </div>
              <div className="stat-row">
                <Metric
                  icon={ShieldCheck}
                  label="Active detectors"
                  value={`${Object.values(state.detectors).filter(Boolean).length} / 4`}
                  foot="Patterns · NLP · OCR · faces"
                />
                <Metric
                  icon={EyeOff}
                  label="Protected findings"
                  value={preview?.findings?.length ?? "—"}
                  foot="Current observation"
                />
                <Metric
                  icon={FileCheck2}
                  label="Privacy receipts"
                  value={receiptCount}
                  foot="Inspected planning payloads"
                />
                <Metric
                  icon={Activity}
                  label="Local processing"
                  value={
                    preview ? `${(preview.latency_ms / 1000).toFixed(2)}s` : "—"
                  }
                  foot="Capture + detection + masking"
                />
              </div>
              <div className="work-grid">
                <section className="panel task-panel">
                  <div className="panel-title">
                    <span className="number">01</span>
                    <h2>Define the task</h2>
                    <span className="mini-tag">CONTRACT FIRST</span>
                  </div>
                  <label className="field-label">Task profile</label>
                  <div className="profile-grid">
                    {profiles.map(([id, label, Icon]) => (
                      <button
                        disabled={active}
                        key={id}
                        className={
                          "profile " + (scenario === id ? "chosen" : "")
                        }
                        onClick={() => {
                          setScenario(id);
                          setTask("");
                        }}
                      >
                        <Icon size={17} />
                        <span>{label}</span>
                        {scenario === id && <Check size={13} />}
                      </button>
                    ))}
                  </div>
                  <label className="field-label" htmlFor="task">
                    What should your agent do?
                  </label>
                  <textarea
                    id="task"
                    value={task}
                    disabled={active}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder={
                      state.scenarios?.[scenario] || "Describe a task…"
                    }
                    rows={4}
                  />
                  <div className="two-fields">
                    <div>
                      <label className="field-label" htmlFor="provider">
                        Planner
                      </label>
                      <select
                        id="provider"
                        value={provider}
                        disabled={active}
                        onChange={(e) => setProvider(e.target.value)}
                      >
                        <option value="demo">Local test driver</option>
                        <option value="gemini">Gemini · cloud AI</option>
                        <option value="ollama">Ollama · local AI</option>
                      </select>
                    </div>
                    <div>
                      <label className="field-label" htmlFor="mode">
                        Disclosure mode
                      </label>
                      <select
                        id="mode"
                        value={mode}
                        disabled={active}
                        onChange={(e) => setMode(e.target.value)}
                      >
                        <option value="contract">Task-bound · minimal</option>
                        <option value="baseline">
                          Baseline · full sanitized text
                        </option>
                      </select>
                    </div>
                  </div>
                  <p className="helper">
                    {provider === "demo"
                      ? "The local test driver checks the pipeline without an AI request. Its results are not AI task-success scores."
                      : provider === "gemini"
                        ? "Only sanitized context reaches Gemini. Add your API key in Settings."
                        : "Requires a running local Ollama instance with qwen3:4b. No cloud fallback."}
                  </p>
                  <div className="button-row">
                    <button
                      className="primary"
                      disabled={busy || active || !ready}
                      onClick={() =>
                        act(() =>
                          api("runs", {
                            scenario,
                            provider,
                            mode,
                            task,
                            seed: 1,
                            layout: 0,
                          }),
                        )
                      }
                    >
                      {busy ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <Play size={16} />
                      )}
                      Start protected task
                      <ArrowRight size={16} />
                    </button>
                    <button
                      className="secondary"
                      disabled={!run}
                      onClick={() => act(() => api("stop", {}))}
                    >
                      <Square size={14} />
                      Stop & clear
                    </button>
                  </div>
                  <div className="contract-foot">
                    <LockKeyhole size={15} />
                    <span>Secrets: local only</span>
                    <span>Approval: enforced</span>
                  </div>
                </section>
                <section className="panel preview-panel">
                  <div className="panel-title">
                    <span className="number">02</span>
                    <h2>Inspect the boundary</h2>
                    <span className="live-dot">
                      {active ? "LIVE" : "PREVIEW"}
                    </span>
                  </div>
                  <div className="preview-toolbar">
                    <div className="segmented">
                      <button
                        className={!raw ? "on" : ""}
                        onClick={() => setRaw(false)}
                      >
                        <ShieldCheck size={14} />
                        Sanitized
                      </button>
                      <button
                        className={raw ? "on" : ""}
                        onClick={() => setRaw(true)}
                      >
                        <Eye size={14} />
                        Original · local
                      </button>
                    </div>
                    <span>
                      {preview ? "1280 × 900" : "Awaiting observation"}
                    </span>
                  </div>
                  <div className={"preview " + (raw ? "raw" : "")}>
                    {preview ? (
                      <img
                        src={raw ? preview.original : preview.sanitized}
                        alt={
                          raw
                            ? "Original webpage visible only on your device"
                            : "Locally sanitized webpage"
                        }
                      />
                    ) : (
                      <div className="preview-empty">
                        <div className="empty-illustration">
                          <ScanEye size={38} />
                          <span />
                          <span />
                        </div>
                        <h3>Your agent’s view starts here</h3>
                        <p>
                          Start a task to see sensitive information
                          <br />
                          removed before reasoning begins.
                        </p>
                        <div className="empty-label">
                          <LockKeyhole size={12} /> ORIGINAL PIXELS STAY LOCAL
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="preview-bottom">
                    <span>
                      <i className="green-dot" />
                      {raw
                        ? "Local preview — never exported"
                        : "Sanitized preview — image disclosure requires approval"}
                    </span>
                    <span>{preview?.masks?.length ?? 0} masks</span>
                  </div>
                </section>
              </div>
              {run?.approval && (
                <div className="approval">
                  <div className="approval-icon">
                    <LockKeyhole />
                  </div>
                  <div>
                    <div className="eyebrow">YOUR DECISION</div>
                    <h3>{run.approval.title}</h3>
                    <p>
                      Permission applies to this action and snapshot only. The
                      page is checked again before execution.
                    </p>
                  </div>
                  <button
                    className="secondary"
                    onClick={() =>
                      act(() =>
                        api("approve", {
                          approval_id: run.approval.id,
                          approved: false,
                        }),
                      )
                    }
                  >
                    Decline
                  </button>
                  <button
                    className="primary"
                    onClick={() =>
                      act(() =>
                        api("approve", {
                          approval_id: run.approval.id,
                          approved: true,
                        }),
                      )
                    }
                  >
                    Approve once <Check size={16} />
                  </button>
                </div>
              )}
              <div className="lower-grid">
                <section className="panel">
                  <div className="panel-title">
                    <h2>Activity timeline</h2>
                    <span className={"run-state " + (run?.status || "idle")}>
                      {run?.status?.replace("_", " ") || "Ready when you are"}
                    </span>
                  </div>
                  <div className="timeline">
                    {run?.events?.length ? (
                      run.events
                        .slice(-8)
                        .reverse()
                        .map((e: Obj) => (
                          <div className={"event " + e.kind} key={e.id}>
                            <span className="event-dot" />
                            <div>
                              <strong>{e.title}</strong>
                              <p>{e.detail}</p>
                            </div>
                            <time>{e.time}</time>
                          </div>
                        ))
                    ) : (
                      <p className="blank-copy">
                        Every capture, disclosure and action will appear here.
                      </p>
                    )}
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-title">
                    <h2>Why it was protected</h2>
                    <span className="mini-tag">EXPLAINABLE</span>
                  </div>
                  <div className="findings">
                    {preview?.findings?.length ? (
                      preview.findings.slice(0, 8).map((f: Obj, i: number) => (
                        <div className="finding" key={i}>
                          <LockKeyhole size={15} />
                          <div>
                            <strong>{f.kind.replaceAll("_", " ")}</strong>
                            <small>{f.reason}</small>
                          </div>
                          <span>{f.source.split("/")[0]}</span>
                        </div>
                      ))
                    ) : (
                      <p className="blank-copy">
                        Detection reasons appear after the first observation.
                        Raw values are never listed here.
                      </p>
                    )}
                  </div>
                </section>
              </div>
            </>
          )}
          {tab === "contract" && (
            <>
              <PageTitle
                eyebrow="TRUST, MADE EXPLICIT"
                title="A contract for every task."
                text="The model can propose. Local policy decides what it can see and do."
              />
              <div className="contract-grid">
                {[
                  [
                    "01",
                    "Minimal by default",
                    "Task-bound mode sends semantic controls and public completion status. Additional image context needs a specific region and your approval.",
                    ScanEye,
                  ],
                  [
                    "02",
                    "Secrets are capabilities",
                    "A secret reference is bound to its task, origin and field purpose, with a limited use count. It never becomes a value the planner can read.",
                    KeyRound,
                  ],
                  [
                    "03",
                    "Approval expires with context",
                    "Sensitive operations are paused for approval. A changed page, stale snapshot or unavailable target invalidates execution.",
                    Fingerprint,
                  ],
                  [
                    "04",
                    "Receipts, not promises",
                    "Each planning payload has a digest and disclosure record. A receipt proves what this app checked; it does not prove perfect PII detection.",
                    FileCheck2,
                  ],
                ].map(([n, title, body, Icon]: any) => (
                  <section className="panel principle" key={n}>
                    <span className="principle-number">{n}</span>
                    <Icon size={28} />
                    <h2>{title}</h2>
                    <p>{body}</p>
                  </section>
                ))}
              </div>
              <section className="panel flow-panel">
                <h2>The data boundary</h2>
                <div className="flow">
                  {[
                    "Local browser",
                    "Detect & sanitize",
                    "Contract + gate",
                    "Reasoning",
                    "Validate action",
                  ].map((s, i) => (
                    <React.Fragment key={s}>
                      <span className={i === 3 ? "cloud" : ""}>{s}</span>
                      {i < 4 && <ArrowRight size={18} />}
                    </React.Fragment>
                  ))}
                </div>
                <p className="helper">
                  This protects the application’s model pathway. Authorized
                  websites still receive submitted form values. Other
                  applications and a compromised OS are outside the boundary.
                </p>
              </section>
            </>
          )}
          {tab === "attacks" && (
            <>
              <PageTitle
                eyebrow="DON’T JUST CLAIM IT. CHALLENGE IT."
                title="Put the boundary to the test."
                text="Synthetic probes exercise the real local policy and payload checks. No external attack requests are sent."
              />
              <div className="lab-banner">
                <div>
                  <FlaskConical size={30} />
                  <h2>Adversarial probe suite</h2>
                  <p>
                    Secret exfiltration · wrong-origin use · unsupported actions
                    · schema abuse
                  </p>
                </div>
                <button
                  className="primary"
                  disabled={busy || !ready}
                  onClick={() =>
                    act(async () => setAttack(await api("attack-lab", {})))
                  }
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Play size={17} />
                  )}
                  Run attack probes
                </button>
              </div>
              {attack && (
                <>
                  <div className="stat-row">
                    <Metric
                      icon={ShieldCheck}
                      label="Blocked probes"
                      value={`${attack.blocked}/${attack.total}`}
                      foot="Measured local enforcement"
                    />
                    <Metric
                      icon={Globe}
                      label="External requests"
                      value={attack.external_requests}
                      foot="Synthetic local test only"
                    />
                    <Metric
                      icon={FlaskConical}
                      label="Test scope"
                      value="Policy"
                      foot="Not full prompt-injection accuracy"
                    />
                  </div>
                  <section className="panel">
                    <table>
                      <thead>
                        <tr>
                          <th>Attack</th>
                          <th>Enforcement layer</th>
                          <th>Result</th>
                          <th>Latency</th>
                        </tr>
                      </thead>
                      <tbody>
                        {attack.results.map((r: Obj) => (
                          <tr key={r.name}>
                            <td>{r.name}</td>
                            <td>{r.layer}</td>
                            <td>
                              <span
                                className={
                                  "result " + (r.blocked ? "pass" : "fail")
                                }
                              >
                                {r.blocked ? "Blocked" : "Not blocked"}
                              </span>
                            </td>
                            <td>{r.latency_ms} ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="helper">{attack.scope}</p>
                  </section>
                </>
              )}
            </>
          )}
          {tab === "evidence" && (
            <>
              <PageTitle
                eyebrow="MEASURED, NOT ASSUMED"
                title="Evidence you can explain."
                text="Reproducible detection results and an inspectable record of every planning payload."
              />
              <div className="button-row evidence-actions">
                <button
                  className="primary"
                  disabled={busy || active || !ready}
                  onClick={() =>
                    act(async () => setReport(await api("evaluate", {})))
                  }
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Play size={16} />
                  )}
                  Run text evaluation
                </button>
                <button className="secondary" onClick={() => act(download)}>
                  <Download size={16} />
                  Export sanitized evidence
                </button>
              </div>
              {report && (
                <>
                  <div className="stat-row">
                    <Metric
                      icon={ScanEye}
                      label="Entity recall"
                      value={`${(report.recall * 100).toFixed(1)}%`}
                      foot={`${report.true_positives} detected · ${report.false_negatives} missed`}
                    />
                    <Metric
                      icon={ShieldCheck}
                      label="Entity precision"
                      value={`${(report.precision * 100).toFixed(1)}%`}
                      foot={`${report.false_positives} false detections`}
                    />
                    <Metric
                      icon={FileCheck2}
                      label="Synthetic text cases"
                      value={report.total_cases}
                      foot="5 scenarios · 2 layouts · 5 seeds"
                    />
                    <Metric
                      icon={Activity}
                      label="Detector p95"
                      value={`${report.p95_ms}ms`}
                      foot="Text only; excludes capture and AI"
                    />
                  </div>
                  <div className="notice">
                    <AlertTriangle size={18} />
                    {report.scope}
                  </div>
                </>
              )}
              <section className="panel receipts">
                <div className="panel-title">
                  <h2>Privacy receipts</h2>
                  <span className="mini-tag">CURRENT SESSION</span>
                </div>
                {run?.receipts?.length ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Decision / destination</th>
                        <th>Disclosure</th>
                        <th>Bytes</th>
                        <th>Payload digest</th>
                      </tr>
                    </thead>
                    <tbody>
                      {run.receipts.map((r: Obj) => (
                        <tr key={r.id}>
                          <td>
                            <span
                              className={
                                "result " +
                                (r.decision === "allowed" ? "pass" : "fail")
                              }
                            >
                              {r.decision}
                            </span>
                            <small className="table-small">
                              {r.destination || r.reason}
                            </small>
                          </td>
                          <td>
                            {r.image_disclosed
                              ? `Approved region ${r.region}`
                              : "Text only"}
                          </td>
                          <td>{r.bytes}</td>
                          <td className="mono" title={r.digest}>
                            {r.digest
                              ? r.digest.slice(0, 18) + "…"
                              : "Not transmitted"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="blank-copy">
                    Run a task to create privacy receipts. No sample results are
                    displayed.
                  </p>
                )}
              </section>
            </>
          )}
          <footer>
            <span>
              <ShieldCheck size={14} /> PrivacyLens · task-bound privacy for
              browser agents
            </span>
            <span>Built for evidence. Designed for trust.</span>
          </footer>
        </div>
      </main>
      {settings && (
        <div className="modal-backdrop">
          <section className="modal">
            <button
              className="close icon"
              onClick={() => setSettings(false)}
              aria-label="Close settings"
            >
              <X />
            </button>
            <div className="eyebrow">THIS DEVICE ONLY</div>
            <h2>Workspace settings</h2>
            <p className="helper">
              Keys and secret overrides are held in backend memory. They are
              never returned to the dashboard or saved to source files.
            </p>
            <label className="field-label">Gemini API key</label>
            <p className="helper" role="status">
              {state.provider_status?.provider === "gemini"
                ? state.provider_status.message
                : state.gemini_configured
                  ? "Key saved locally. Provider access is checked when a task runs."
                  : "No Gemini key is saved in this session."}
            </p>
            <input
              type="password"
              autoComplete="off"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder={
                state.gemini_configured
                  ? "A key is already configured"
                  : "Paste key locally"
              }
            />
            <label className="field-label">Gemini model</label>
            <input value={model} onChange={(e) => setModel(e.target.value)} />
            <label className="check">
              <input
                type="checkbox"
                checked={visibleBrowser}
                onChange={(e) => setVisibleBrowser(e.target.checked)}
              />{" "}
              Show the controlled browser window
            </label>
            <button
              className="primary"
              disabled={active || busy}
              onClick={() =>
                act(async () => {
                  await api("settings", {
                    api_key: key,
                    gemini_model: model,
                    headless: !visibleBrowser,
                  });
                  setKey("");
                  setSettings(false);
                })
              }
            >
              Save session settings <Check size={16} />
            </button>
            <hr />
            <h3>Local secret override</h3>
            <p className="helper">
              Synthetic scenarios already include test values. Use only demo
              credentials for the hackathon.
            </p>
            <div className="two-fields">
              <select
                value={secretRef}
                onChange={(e) => setSecretRef(e.target.value)}
              >
                {[
                  "password",
                  "username",
                  "email",
                  "otp",
                  "name",
                  "address",
                  "card",
                  "cvv",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <input
                type="password"
                value={secretValue}
                onChange={(e) => setSecretValue(e.target.value)}
                placeholder="Local value"
              />
            </div>
            <button
              className="secondary"
              disabled={active || !secretValue}
              onClick={() =>
                act(async () => {
                  await api("secrets", {
                    reference: secretRef,
                    value: secretValue,
                  });
                  setSecretValue("");
                })
              }
            >
              Store in memory
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
function Metric({ icon: Icon, label, value, foot }: any) {
  return (
    <div className="metric">
      <div>
        <span>{label}</span>
        <Icon size={17} />
      </div>
      <strong>{value}</strong>
      <small>{foot}</small>
    </div>
  );
}
function PageTitle({ eyebrow, title, text }: any) {
  return (
    <div className="section-heading">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{text}</p>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
