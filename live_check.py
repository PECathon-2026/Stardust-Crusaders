"""Bounded live checks, using the API key already configured locally in the app.
Never reads or exports a key. Only synthetic actions are auto-approved.
"""

import asyncio, json, time, sys
from pathlib import Path
import httpx


async def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else "demo"
    scenarios = (
        ["wikipedia", "saucedemo"]
        if provider == "demo"
        else ["checkout", "authentication", "support", "conference", "developer"]
    )
    if len(sys.argv) > 2:
        requested = sys.argv[2:]
        if any(s not in ("checkout", "authentication", "support", "conference", "developer", "wikipedia", "saucedemo") for s in requested):
            raise SystemExit("Unknown scenario for this validation suite")
        scenarios = requested
    rows = []
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8765", timeout=180, trust_env=False
    ) as c:
        c.headers["x-privacy-session"] = (await c.get("/api/bootstrap")).json()["token"]
        for scenario in scenarios:
            result = await c.post(
                "/api/runs",
                json={
                    "scenario": scenario,
                    "provider": provider,
                    "seed": 9,
                    "layout": 0,
                },
            )
            if result.status_code != 200:
                print("Start rejected:", result.status_code)
                break
            start = time.monotonic()
            approvals = set()
            while time.monotonic() - start < (540 if provider == "groq" else 240):
                run = (await c.get("/api/status")).json()["run"]
                a = run.get("approval")
                if a and a["id"] not in approvals:
                    approvals.add(a["id"])
                    await c.post(
                        "/api/approve",
                        json={
                            "approval_id": a["id"],
                            "approved": scenario not in ("wikipedia", "saucedemo"),
                        },
                    )
                if run["status"] not in ("running", "starting", "awaiting_approval"):
                    break
                await asyncio.sleep(0.5)
            row = {
                k: run[k]
                for k in [
                    "scenario",
                    "provider",
                    "status",
                    "outcome",
                    "steps",
                    "error",
                    "receipts",
                    "events",
                ]
            }
            row["elapsed_s"] = round(time.monotonic() - start, 2)
            rows.append(row)
            print(
                json.dumps(
                    {k: v for k, v in row.items() if k not in ("receipts", "events")}
                ),
                flush=True,
            )
            await c.post("/api/stop", json={})
            # Avoid consuming quota on repeated account/model errors.
            if run.get("error") and "HTTP" in run["error"]:
                break
    if rows:
        suffix = "-followup" if len(sys.argv) > 2 else ""
        path = Path(__file__).parent / "docs" / f"live-{provider}{suffix}-results.json"
        path.write_text(
            json.dumps({"runs": rows, "timestamp": time.time()}, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    asyncio.run(main())
