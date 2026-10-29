import json, time, statistics
from dataclasses import asdict
from .fixtures import values
from .privacy import PrivacyError, leak_check
from .agent import PermitVault
from .contracts import Action


def attack_lab(detector):
    results = []
    vault = PermitVault("authentication", "http://127.0.0.1:8766", values())
    probes = [
        (
            "Secret in outgoing text",
            "Payload gateway",
            lambda: leak_check(
                json.dumps({"text": values()["password"]}).encode(),
                list(values().values()),
                detector,
            ),
        ),
        (
            "Secret sent as URL query",
            "Payload gateway",
            lambda: leak_check(
                json.dumps(
                    {"url": "https://attacker.invalid/?q=" + values()["api_key"]}
                ).encode(),
                list(values().values()),
                detector,
            ),
        ),
        (
            "Secret in wrong field",
            "Secret permission",
            lambda: vault.resolve("password", "email", vault.origin),
        ),
        (
            "Secret on wrong origin",
            "Secret permission",
            lambda: vault.resolve("password", "password", "https://attacker.invalid"),
        ),
        (
            "Arbitrary JavaScript action",
            "Action schema",
            lambda: Action.model_validate(
                {"type": "javascript", "snapshot_id": "s", "text": "document.cookie"}
            ),
        ),
        (
            "Extra action properties",
            "Action schema",
            lambda: Action.model_validate(
                {
                    "type": "click",
                    "snapshot_id": "s",
                    "target_id": "e1",
                    "url": "https://attacker.invalid",
                }
            ),
        ),
        (
            "Guessed target with text injection",
            "Action schema",
            lambda: Action.model_validate(
                {
                    "type": "click",
                    "snapshot_id": "s",
                    "target_id": "e1",
                    "text": "reconstruct the secret",
                }
            ),
        ),
        (
            "Unsupported secret capability",
            "Secret permission",
            lambda: vault.resolve("api_key", "api_key", vault.origin),
        ),
    ]
    for name, layer, probe in probes:
        start = time.perf_counter()
        blocked = False
        try:
            probe()
        except (PrivacyError, ValueError):
            blocked = True
        results.append(
            {
                "name": name,
                "layer": layer,
                "blocked": blocked,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
    return {
        "results": results,
        "blocked": sum(r["blocked"] for r in results),
        "total": len(results),
        "external_requests": 0,
        "scope": "Local enforcement probes with synthetic data. Not an end-to-end prompt-injection benchmark.",
    }


def evaluate_text(detector):
    start = time.perf_counter()
    cases = []
    tp = fp = fn = 0
    latencies = []
    for scenario in [
        "checkout",
        "authentication",
        "support",
        "conference",
        "developer",
    ]:
        for layout in range(2):
            for seed in range(1, 6):
                v = values(seed)
                selected = {
                    "checkout": ["card", "address"],
                    "authentication": ["email", "phone"],
                    "support": ["phone", "email"],
                    "conference": ["email", "phone"],
                    "developer": ["api_key", "ip", "pan"],
                }[scenario]
                text = ("\n" if layout else " | ").join(
                    f"{key}: {v[key]}" for key in selected
                )
                expected = []
                for key in selected:
                    pos = text.index(v[key])
                    expected.append((pos, pos + len(v[key])))
                t = time.perf_counter()
                fs = detector.detect(text)
                latencies.append((time.perf_counter() - t) * 1000)
                matched = set()
                extra = 0
                for f in fs:
                    hits = [
                        i
                        for i, (a, b) in enumerate(expected)
                        if f.start <= a and f.end >= b
                    ]
                    if hits:
                        matched.update(hits)
                    else:
                        extra += 1
                tp += len(matched)
                fn += len(expected) - len(matched)
                fp += extra
                cases.append(
                    {
                        "scenario": scenario,
                        "layout": layout,
                        "seed": seed,
                        "expected": len(expected),
                        "detected": len(matched),
                        "false_positives": extra,
                    }
                )
    negatives = [
        "Order ORD-2026-114 costs 1299 rupees.",
        "Build version 1.4.2.",
        "Select Billing to continue.",
        "Quantity: 3. Discount: 15%.",
    ]
    for text in negatives:
        fp += len(detector.detect(text))
    return {
        "suite": "Text detection / synthetic corpus",
        "scope": "50 text cases plus 4 negative controls. Does not measure pixel coverage or AI task success.",
        "cases": cases,
        "total_cases": len(cases),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "recall": round(tp / (tp + fn), 4) if tp + fn else 0,
        "precision": round(tp / (tp + fp), 4) if tp + fp else 0,
        "p50_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 2),
        "elapsed_s": round(time.perf_counter() - start, 2),
        "timestamp": time.time(),
        "attacks": attack_lab(detector),
    }
