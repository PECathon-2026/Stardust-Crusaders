"""Record a captioned synthetic local-driver demo. Requires a running idle app.
Never records Settings or a real account. No cloud requests are made.
"""

import asyncio, json, time
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
from backend.browser import launch_options

ROOT = Path(__file__).parent


async def main():
    async with (
        httpx.AsyncClient(
            base_url="http://127.0.0.1:8765", timeout=180, trust_env=False
        ) as c,
        async_playwright() as pw,
    ):
        c.headers["x-privacy-session"] = (await c.get("/api/bootstrap")).json()["token"]
        state = (await c.get("/api/status")).json()
        assert not state.get("run") or state["run"]["status"] not in (
            "running",
            "starting",
            "awaiting_approval",
        ), "Finish the active task first"
        b = await pw.chromium.launch(**launch_options(pw))
        context = await b.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=str(ROOT / "work" / "videos"),
            record_video_size={"width": 1440, "height": 1000},
        )
        page = await context.new_page()
        await page.goto("http://127.0.0.1:8765")
        await page.wait_for_timeout(1800)
        started = time.monotonic()

        async def caption(text):
            await page.evaluate(
                """text=>{let e=document.getElementById('demo-caption');if(!e){e=document.createElement('div');e.id='demo-caption';e.style='position:fixed;bottom:16px;left:260px;right:24px;z-index:9999;padding:16px 24px;background:#123e36;color:white;border-radius:12px;font:17px Arial;box-shadow:0 4px 24px #0003;pointer-events:none';document.body.append(e)}e.textContent=text}""",
                text,
            )

        await caption(
            "PrivacyLens • Synthetic demonstration • Deterministic local test driver, not cloud AI"
        )
        await page.wait_for_timeout(5000)
        for scenario in [
            "checkout",
            "authentication",
            "support",
            "conference",
            "developer",
        ]:
            await page.get_by_role("button", name="Agent workspace", exact=True).click()
            await c.post(
                "/api/runs",
                json={"scenario": scenario, "provider": "demo", "seed": 1, "layout": 0},
            )
            await caption(
                f"{scenario.title()}: raw data stays local; the planner receives semantic controls and protected references."
            )
            await page.wait_for_timeout(1500)
            await page.evaluate('window.scrollTo({top:430,behavior:"smooth"})')
            start = time.monotonic()
            approved = set()
            while time.monotonic() - start < 100:
                run = (await c.get("/api/status")).json()["run"]
                if run.get("approval") and run["approval"]["id"] not in approved:
                    approved.add(run["approval"]["id"])
                    await caption(
                        "Consequential action paused. Approval applies only to this action and unchanged page snapshot."
                    )
                    await page.wait_for_timeout(2500)
                    await page.get_by_role(
                        "button", name="Approve once", exact=False
                    ).click()
                if run["status"] not in ("running", "starting", "awaiting_approval"):
                    break
                await asyncio.sleep(0.5)
            await caption(
                f"{scenario.title()}: {run['status']} • observed outcome: {run.get('outcome') or 'not verified'}"
            )
            await page.wait_for_timeout(2500)
            await c.post("/api/stop", json={})
        await page.get_by_role("button", name="Attack lab", exact=True).click()
        await page.evaluate("window.scrollTo(0,0)")
        await caption(
            "Attack lab: real local enforcement probes. These are not a comprehensive prompt-injection benchmark."
        )
        await page.get_by_role("button", name="Run attack probes").click()
        await page.wait_for_timeout(6000)
        await page.get_by_role("button", name="Privacy contract", exact=True).click()
        await page.evaluate("window.scrollTo(0,0)")
        await caption(
            "Original workflow: minimal disclosure + scoped secrets + snapshot approvals + inspectable request receipts."
        )
        await page.wait_for_timeout(6000)
        await page.get_by_role("button", name="Evidence & results", exact=True).click()
        await page.get_by_role("button", name="Run text evaluation").click()
        await page.wait_for_timeout(4000)
        await caption(
            "Results are measured, not guarantees. Screenshot coverage, live AI and external-site results are reported separately."
        )
        remaining = max(5, 130 - (time.monotonic() - started))
        await page.wait_for_timeout(min(remaining, 30) * 1000)
        video = page.video
        await context.close()
        await video.save_as(str(ROOT / "docs" / "privacylens-demo.webm"))
        await b.close()
        print(
            json.dumps(
                {
                    "video": "docs/privacylens-demo.webm",
                    "duration_seconds": round(time.monotonic() - started),
                    "planner": "local deterministic test driver",
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
