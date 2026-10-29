"""Independent annotated screenshot evaluation. Requires fixture server on 8766.
Ground truth is used only after capture, never supplied to the detector.
"""

import asyncio, json, time, statistics
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from backend.privacy import Detector
from backend.browser import Browser
from backend.fixtures import fixture

ROOT = Path(__file__).parent


def coverage(shape, boxes):
    im = Image.new("1", shape)
    d = ImageDraw.Draw(im)
    for b in boxes:
        d.rectangle(
            (
                max(0, int(b["x"]) - 3),
                max(0, int(b["y"]) - 3),
                min(shape[0], int(b["x"] + b["width"]) + 4),
                min(shape[1], int(b["y"] + b["height"]) + 4),
            ),
            fill=1,
        )
    return np.asarray(im, dtype=bool)


async def main():
    d = Detector()
    d.initialize()
    assert all(d.status.values()), d.status
    b = Browser(d)
    rows = []
    try:
        await b.open("http://127.0.0.1:8766/scenario/checkout")
        for scenario in [
            "checkout",
            "authentication",
            "support",
            "conference",
            "developer",
        ]:
            for layout in range(2):
                for seed in range(11, 16):
                    await b.page.goto(
                        f"http://127.0.0.1:8766/scenario/{scenario}?seed={seed}&layout={layout}"
                    )
                    await b.page.wait_for_timeout(100)
                    p = await b.capture(known=(), mode="baseline")
                    _, truth, _ = fixture(scenario, seed, layout)
                    boxes = await b.page.evaluate(
                        """truth=>truth.map(([kind,value])=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const boxes=[];while(n=w.nextNode()){if(n.parentElement.closest('script,style'))continue;let i=n.textContent.indexOf(value);if(i<0)continue;const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+value.length);for(const b of r.getClientRects())if(b.y>=0&&b.bottom<=innerHeight)boxes.push({x:b.x,y:b.y,width:b.width,height:b.height});}return {kind,boxes}})""",
                        truth,
                    )
                    masks = coverage((1280, 900), p["masks"])
                    entities = []
                    for item in boxes:
                        if not item["boxes"]:
                            continue
                        expected = coverage((1280, 900), item["boxes"])
                        total = int(expected.sum())
                        rate = float((masks & expected).sum() / total) if total else 0
                        entities.append(
                            {
                                "kind": item["kind"],
                                "coverage": round(rate, 4),
                                "protected": rate >= 0.98,
                            }
                        )
                    row = {
                        "scenario": scenario,
                        "layout": layout,
                        "seed": seed,
                        "entities": entities,
                        "latency_ms": p["latency_ms"],
                        "masked_pixel_fraction": round(float(masks.mean()), 4),
                        "yunet_faces": sum(x["source"] == "yunet" for x in p["masks"]),
                    }
                    rows.append(row)
                    print(
                        json.dumps(
                            {
                                "scenario": scenario,
                                "layout": layout,
                                "seed": seed,
                                "protected": sum(e["protected"] for e in entities),
                                "total": len(entities),
                                "latency_ms": p["latency_ms"],
                            }
                        ),
                        flush=True,
                    )
                    if scenario == "conference" and layout == 0 and seed == 11:
                        (ROOT / "docs" / "conference-sanitized.png").write_bytes(b.png)
    finally:
        await b.close()
    es = [e for r in rows for e in r["entities"]]
    lat = [r["latency_ms"] for r in rows]
    report = {
        "scope": "50 actual browser screenshots, unseen seeds 11–15, two layouts. Detector receives no known-value vault. Coverage covers annotated visible text; whole media is conservatively masked. Not a universal pixel-PII benchmark.",
        "cases": rows,
        "entity_regions": len(es),
        "protected_regions": sum(e["protected"] for e in es),
        "region_recall": sum(e["protected"] for e in es) / len(es),
        "p50_ms": statistics.median(lat),
        "p95_ms": sorted(lat)[int(0.95 * (len(lat) - 1))],
        "mean_masked_fraction": statistics.mean(
            r["masked_pixel_fraction"] for r in rows
        ),
    }
    (ROOT / "docs" / "pixel-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
