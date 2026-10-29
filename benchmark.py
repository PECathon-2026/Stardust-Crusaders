"""Run against start.ps1. Only synthetic fixtures and local deterministic driver.
Auto-approves synthetic actions for tests; this does not change app approval policy.
"""

import asyncio, json, time, statistics
from pathlib import Path
import httpx

ROOT = Path(__file__).parent


async def main():
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8765", timeout=180, trust_env=False
    ) as c:
        c.headers["x-privacy-session"] = (await c.get("/api/bootstrap")).json()["token"]
        while (await c.get("/api/status")).json()["initializing"]:
            await asyncio.sleep(1)
        text = (await c.post("/api/evaluate", json={})).json()
        rows = []
        for mode in ["contract", "baseline"]:
            for scenario in [
                "checkout",
                "authentication",
                "support",
                "conference",
                "developer",
            ]:
                t = time.monotonic()
                r = await c.post(
                    "/api/runs",
                    json={
                        "scenario": scenario,
                        "provider": "demo",
                        "mode": mode,
                        "seed": 7,
                        "layout": 1,
                    },
                )
                r.raise_for_status()
                seen = set()
                latencies = []
                disclosed = []
                approvals = set()
                while time.monotonic() - t < 240:
                    run = (await c.get("/api/status")).json()["run"]
                    p = run.get("preview")
                    if p and p["observation"]["snapshot_id"] not in seen:
                        seen.add(p["observation"]["snapshot_id"])
                        latencies.append(p["latency_ms"])
                        disclosed.append(p["disclosed_text_bytes"])
                    if run.get("approval") and run["approval"]["id"] not in approvals:
                        approvals.add(run["approval"]["id"])
                        await c.post(
                            "/api/approve",
                            json={
                                "approval_id": run["approval"]["id"],
                                "approved": True,
                            },
                        )
                    if run["status"] not in [
                        "running",
                        "starting",
                        "awaiting_approval",
                    ]:
                        break
                    await asyncio.sleep(0.25)
                row = {
                    "scenario": scenario,
                    "mode": mode,
                    "seed": 7,
                    "layout": 1,
                    "status": run["status"],
                    "outcome": run["outcome"],
                    "steps": run["steps"],
                    "approvals": len(approvals),
                    "error": run["error"],
                    "elapsed_s": round(time.monotonic() - t, 2),
                    "processing_ms": latencies,
                    "context_bytes": sum(disclosed),
                    "payload_bytes": sum(r["bytes"] for r in run["receipts"]),
                    "receipts": run["receipts"],
                }
                rows.append(row)
                print(
                    json.dumps(
                        {
                            k: v
                            for k, v in row.items()
                            if k not in ["receipts", "processing_ms"]
                        }
                    ),
                    flush=True,
                )
                await c.post("/api/stop", json={})
        report = {
            "scope": "Local deterministic driver, synthetic pages; not AI task-success evidence. Both modes share the same privacy enforcement. Layout 1 / seed 7 are browser holdout variants.",
            "text": text,
            "runs": rows,
            "timestamp": time.time(),
        }
        (ROOT / "docs" / "benchmark-results.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print("Saved docs/benchmark-results.json", flush=True)


async def direct_main():
    from backend.privacy import Detector
    from backend.browser import Browser
    from backend.agent import Gateway, Run
    from backend.contracts import StartRequest, DEFAULT_TASKS
    from backend.fixtures import values
    from backend.evaluation import evaluate_text

    d = Detector()
    d.initialize()
    assert all(d.status.values()), d.status
    text = evaluate_text(d)
    rows = []
    for mode in ["contract", "baseline"]:
        for scenario in [
            "checkout",
            "authentication",
            "support",
            "conference",
            "developer",
        ]:
            b = Browser(d)
            req = StartRequest(
                scenario=scenario,
                provider="demo",
                mode=mode,
                seed=7,
                layout=1,
                task=DEFAULT_TASKS[scenario],
            )
            url = f"http://127.0.0.1:8766/scenario/{scenario}?seed=7&layout=1"
            run = Run(req, b, Gateway(d), values(7), url)
            start = time.monotonic()
            task = asyncio.create_task(run.loop(url))
            seen = set()
            approvals = set()
            latencies = []
            disclosed = []
            while not task.done():
                p = run.preview
                if p and p["observation"]["snapshot_id"] not in seen:
                    seen.add(p["observation"]["snapshot_id"])
                    latencies.append(p["latency_ms"])
                    disclosed.append(p["disclosed_text_bytes"])
                if run.approval and run.approval["id"] not in approvals:
                    approvals.add(run.approval["id"])
                    run.pending = True
                    run.decision.set()
                await asyncio.sleep(0.1)
            await task
            p = run.preview
            if p and p["observation"]["snapshot_id"] not in seen:
                latencies.append(p["latency_ms"])
                disclosed.append(p["disclosed_text_bytes"])
            row = {
                "scenario": scenario,
                "mode": mode,
                "seed": 7,
                "layout": 1,
                "status": run.status,
                "outcome": run.outcome,
                "steps": run.steps,
                "approvals": len(approvals),
                "error": run.error,
                "elapsed_s": round(time.monotonic() - start, 2),
                "processing_ms": latencies,
                "context_bytes": sum(disclosed),
                "payload_bytes": sum(r["bytes"] for r in run.receipts),
                "receipts": run.receipts,
            }
            rows.append(row)
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in row.items()
                        if k not in ["receipts", "processing_ms"]
                    }
                ),
                flush=True,
            )
            await b.close()
    report = {
        "scope": "Local deterministic driver exercising the same Run/Browser classes in a separate test session. Not AI success evidence. Layout 1 / seed 7 browser variants; full privacy checks enabled in both modes.",
        "text": text,
        "runs": rows,
        "timestamp": time.time(),
    }
    (ROOT / "docs" / "benchmark-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    import sys

    asyncio.run(main() if "--api" in sys.argv else direct_main())
