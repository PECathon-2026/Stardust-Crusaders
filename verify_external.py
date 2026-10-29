"""Live Wikipedia and SauceDemo smoke checks using the deterministic driver.
Runs separately from the dashboard. Never performs a purchase or sends a message.
"""

import asyncio, json, time
import sys
from pathlib import Path
from backend.privacy import Detector
from backend.browser import Browser
from backend.agent import Run, Gateway
from backend.contracts import StartRequest, DEFAULT_TASKS
from backend.fixtures import values


async def main():
    d = Detector()
    d.initialize()
    rows = []
    for scenario, url in [
        ("wikipedia", "https://en.wikipedia.org/wiki/Main_Page"),
        ("saucedemo", "https://www.saucedemo.com/"),
    ]:
        if len(sys.argv) > 1 and scenario != sys.argv[1]:
            continue
        b = Browser(d)
        v = values(1)
        if scenario == "saucedemo":
            v["password"] = v["sauce_password"]
        run = Run(
            StartRequest(scenario=scenario, task=DEFAULT_TASKS[scenario]),
            b,
            Gateway(d),
            v,
            url,
        )
        task = asyncio.create_task(run.loop(url))
        start = time.monotonic()
        while not task.done():
            if run.approval:
                run.pending = False
                run.decision.set()
            await asyncio.sleep(0.2)
        await task
        row = {
            k: run.public()[k]
            for k in [
                "scenario",
                "provider",
                "status",
                "outcome",
                "steps",
                "error",
                "receipts",
            ]
        }
        row["elapsed_s"] = round(time.monotonic() - start, 2)
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "receipts"}), flush=True)
        if run.status != "completed":
            print(
                json.dumps(
                    {
                        "history": run.history,
                        "observation": run.preview["observation"]
                        if run.preview
                        else None,
                    }
                ),
                flush=True,
            )
            if b.png:
                (
                    Path(__file__).parent / "work" / f"{scenario}-blocked.png"
                ).write_bytes(b.png)
        await b.close()
    (Path(__file__).parent / "docs" / "live-demo-results.json").write_text(
        json.dumps(
            {
                "scope": "Live external websites, deterministic driver, independently checked outcomes; not AI task success",
                "runs": rows,
                "timestamp": time.time(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
