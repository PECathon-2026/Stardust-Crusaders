import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  Settings,
  ArrowUpRight,
  Play,
  Square,
  LockKeyhole,
  Check,
  X,
} from "lucide-react";
import "./agent.css";

type Data = Record<string, any>;
let session = "";
async function request(path: string, body?: unknown): Promise<any> {
  if (!session) session = (await (await fetch("/api/bootstrap")).json()).token;
  const send = () =>
    fetch("/api/" + path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "content-type": "application/json",
        "x-privacy-session": session,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  let response = await send();
  if (response.status === 401) {
    session = (await (await fetch("/api/bootstrap")).json()).token;
    response = await send();
  }
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string" ? data.detail : "Request rejected",
    );
  return data;
}

export default function AgentWorkspace() {
  const [state, setState] = useState<Data>({ initializing: true });
  const [pages, setPages] = useState<Data[]>([]);
  const [url, setUrl] = useState("http://127.0.0.1:8766/scenario/support");
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("groq");
  const [settings, setSettings] = useState(false);
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [original, setOriginal] = useState(false);
  useEffect(() => {
    let live = true;
    request("pages")
      .then((d) => {
        if (live) setPages(d.pages);
      })
      .catch((e) => setError(e.message));
    const poll = async () => {
      try {
        const s = await request("status");
        if (live) setState(s);
      } catch (e) {
        if (live) setError((e as Error).message);
      }
    };
    void poll();
    const id = setInterval(poll, 1500);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);
  const run = state.run;
  useEffect(() => {
    const current = pages.find((p) => p.name === state.run?.scenario);
    if (current) setUrl(current.url);
    if (state.run?.provider && state.run.provider !== "demo") setProvider(state.run.provider);
  }, [state.run?.id, pages.length]);
  const active = ["starting", "running", "awaiting_approval"].includes(
    run?.status,
  );
  const preview = run?.preview;
  const configured =
    provider === "groq"
      ? state.groq_configured
      : provider === "gemini"
        ? state.gemini_configured
        : true;
  async function act(fn: () => Promise<any>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      setState(await request("status"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const page = pages.find((p) => p.url === url);
  return (
    <div className="agent-shell">
      <header className="agent-header">
        <a className="agent-brand" href="/">
          <ShieldCheck size={28} />
          PrivacyLens <span>Browser agent</span>
        </a>
        <nav>
          <a href="/lab">
            Privacy Lab <ArrowUpRight size={15} />
          </a>
          <button aria-label="Settings" onClick={() => setSettings(!settings)}>
            <Settings size={18} />
          </button>
        </nav>
      </header>
      <main className="agent-layout">
        <section
          className="agent-browser"
          aria-label="Protected browser preview"
        >
          <div className="agent-address">
            <LockKeyhole size={16} />
            <label htmlFor="page-url">Page</label>
            <input
              id="page-url"
              aria-label="Page URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={active}
            />
          </div>
          <div className="agent-preview-bar">
            <span>
              {original
                ? "Original · stays on this device"
                : "Protected view · what can be disclosed"}
            </span>
            <button onClick={() => setOriginal(!original)} disabled={!preview}>
              {original ? "Show protected view" : "Show local original"}
            </button>
          </div>
          <div className="agent-canvas">
            {preview ? (
              <img
                src={original ? preview.original : preview.sanitized}
                alt={
                  original
                    ? "Original page, local only"
                    : "Sanitized browser page"
                }
              />
            ) : (
              <div className="agent-welcome">
                <ShieldCheck size={52} />
                <span className="agent-kicker">
                  YOUR TASK. YOUR PRIVATE DATA.
                </span>
                <h1>
                  Let AI do the work.
                  <br />
                  Keep your details local.
                </h1>
                <p>
                  Choose a supported page, describe what you need, and watch the
                  agent work through a protected view.
                </p>
                <p className="agent-note">
                  This workspace controls a separate browser session. It does
                  not control tabs in your everyday browser.
                </p>
              </div>
            )}
          </div>
          <footer className="agent-browser-footer">
            <span>{preview?.findings?.length ?? 0} privacy findings</span>
            <span>{run?.steps ?? 0} steps</span>
            {run && <span>{run.provider === "demo" ? "Local test driver · not AI" : run.provider + " planner"}</span>}
            <span>{run?.receipts?.length ?? 0} disclosure receipts</span>
            <a href="/lab">Inspect privacy evidence ↗</a>
          </footer>
        </section>
        <aside className="agent-sidebar" aria-label="Agent sidebar">
          <div className="agent-sidebar-heading">
            <span className="agent-kicker">PRIVATE BY DESIGN</span>
            <h2>What should I do?</h2>
            <p>
              Only sanitized context reaches the planner. Sensitive actions wait
              for your approval.
            </p>
          </div>
          <label htmlFor="supported-page">Supported pages</label>
          <select
            id="supported-page"
            value={page ? url : ""}
            disabled={active}
            onChange={(e) => {
              setUrl(e.target.value);
              setPrompt("");
            }}
          >
            <option value="" disabled>
              Choose a supported page
            </option>
            {pages.map((p) => (
              <option key={p.url} value={p.url}>
                {p.name === "wikipedia"
                  ? "Wikipedia · public website"
                  : p.name === "saucedemo"
                    ? "SauceDemo · public demo"
                    : p.name + " · synthetic demo"}
              </option>
            ))}
          </select>
          <p className="agent-note">
            Arbitrary websites are not enabled in this version.
          </p>
          <label htmlFor="agent-prompt">Your instructions</label>
          <textarea
            id="agent-prompt"
            rows={5}
            placeholder="Tell me what to do on this page…"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={active}
            maxLength={2000}
          />
          <button
            className="agent-example"
            disabled={active || !page}
            onClick={() => {
              if (page)
                setPrompt(
                  page.example.replace(
                    "Choose Billing as the issue category, enter",
                    'Set the issue category to "Billing". Enter',
                  ),
                );
            }}
          >
            Use example prompt
          </button>
          <label htmlFor="agent-provider">AI planner</label>
          <select
            id="agent-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            disabled={active}
          >
            <option value="groq">Groq · sanitized text</option>
            <option value="gemini">Gemini</option>
            <option value="ollama">Ollama · local model required</option>
          </select>
          {!configured && (
            <p className="agent-note">
              Add your {provider === "groq" ? "Groq" : "Gemini"} key in Settings
              first.
            </p>
          )}
          <div className="agent-actions">
            <button
              className="agent-start"
              disabled={
                active ||
                busy ||
                state.initializing ||
                !configured ||
                prompt.trim().length < 3 ||
                !page
              }
              onClick={() =>
                act(() =>
                  request("agent/runs", { url, task: prompt, provider }),
                )
              }
            >
              <Play size={16} />
              Start task
            </button>
            <button
              disabled={!active || busy}
              onClick={() => act(() => request("stop", {}))}
            >
              <Square size={16} />
              Stop
            </button>
          </div>
          <div className="agent-status" role="status">
            {state.initializing
              ? "Preparing local privacy detectors…"
              : active && state.provider_status?.state === "pacing"
                ? "Waiting for the Groq budget. This continues automatically; Stop is available."
                : run?.status === "completed"
                  ? "Verified page outcome: " + run.outcome
                  : run?.status === "needs_review"
                    ? "The planner finished; the task outcome is not independently verified."
                    : run?.status || "Ready for your instructions"}
          </div>
          {(error || run?.error) && (
            <div className="agent-error" role="alert">
              {error || run.error}
            </div>
          )}
          {run?.approval && (
            <section className="agent-approval">
              <h3>Your approval is needed</h3>
              <p>{run.approval.label}</p>
              <p>
                {run.approval.kind === "disclosure"
                  ? "Share this already-sanitized image region with the model?"
                  : "Allow this action on the controlled page?"}
              </p>
              <div className="agent-actions">
                <button
                  disabled={busy}
                  onClick={() =>
                    act(() =>
                      request("approve", {
                        approval_id: run.approval.id,
                        approved: false,
                      }),
                    )
                  }
                >
                  <X size={16} />
                  Decline
                </button>
                <button
                  disabled={busy}
                  onClick={() =>
                    act(() =>
                      request("approve", {
                        approval_id: run.approval.id,
                        approved: true,
                      }),
                    )
                  }
                >
                  <Check size={16} />
                  Approve
                </button>
              </div>
            </section>
          )}
          <section className="agent-activity">
            <h3>Activity</h3>
            {run?.events?.length ? (
              run.events.slice(-5).map((e: Data) => (
                <div key={e.id}>
                  <strong>{e.title}</strong>
                  <p>{e.detail}</p>
                </div>
              ))
            ) : (
              <p>Local detection → sanitized reasoning → validated action.</p>
            )}
          </section>
        </aside>
      </main>
      {settings && (
        <div className="agent-overlay">
          <section
            className="agent-settings"
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
          >
            <button
              className="agent-close"
              aria-label="Close settings"
              onClick={() => {
                setSettings(false);
                setKey("");
              }}
            >
              <X />
            </button>
            <h2 id="settings-title">Session settings</h2>
            <p>
              Keys stay in backend memory and clear on restart. Never paste keys
              into your task prompt.
            </p>
            <label htmlFor="session-key">
              {provider === "gemini" ? "Gemini" : "Groq"} API key
            </label>
            <input
              id="session-key"
              type="password"
              autoComplete="off"
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
            <button
              className="agent-start"
              disabled={active || busy || !key || provider === "ollama"}
              onClick={() =>
                act(async () => {
                  await request("settings", {
                    ...(provider === "gemini"
                      ? { api_key: key }
                      : { groq_api_key: key }),
                    gemini_model: state.gemini_model || "gemini-3.5-flash-lite",
                    groq_model: state.groq_model || "openai/gpt-oss-120b",
                    headless: state.headless ?? true,
                  });
                  setKey("");
                  setSettings(false);
                })
              }
            >
              Save session key
            </button>
            <a href="/lab">Advanced settings and local secret overrides ↗</a>
            {error && <p role="alert">{error}</p>}
          </section>
        </div>
      )}
    </div>
  );
}
