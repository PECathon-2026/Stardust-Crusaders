# Measured evaluation

Measured on this Windows laptop (16 GB RAM, CPU local inference; GTX 1650 is not required). These are hackathon fixture results, not production guarantees. Machine-readable evidence is saved beside this document.

## Current verified results
| Check | Result | Scope |
|---|---|---|
| Automated tests | 56 passed (also verified after moving to D:) | Detector patterns, negative text, payload fields/encodings, image masks, vault use limits, dynamic action schemas, exact-byte mock transport, HTTP failures, API, stale/duplicate/disabled targets, denied/mutated approvals and approved-only sanitized crop disclosure |
| Text detection | 100% recall, 98.21% precision | 110 expected entities across 50 text cases, 4 negative controls; 2 false positives; no known-secret hints |
| Text latency | p50 10.22 ms, p95 19.48 ms | Detector only, excludes browser and AI |
| Screenshot annotated-region coverage | 130/130 regions covered at least 98% | 50 actual screenshots, seeds 11–15, 2 layouts × 5 scenarios; no known-value vault passed to capture |
| Screenshot processing | p50 2,564.5 ms, p95 3,497 ms | Capture, DOM scan, NLP, OCR, face detection and masking; some early samples overlapped other development checks |
| Mean masked viewport fraction | 7.385% | Includes conservative input/media masking; not false-positive pixel rate |
| YuNet conference face detections | 2 per image in all 10 conference samples | Repeated fictional face fixture; not a general face benchmark |
| UI smoke | No page JavaScript errors; no horizontal overflow at 390 px | Desktop and mobile dashboard inspection |

The p95 screenshot target of <3 seconds is **not met** in this run. All annotated regions being covered does not establish zero unknown-PII leakage. Small, split, transformed or occluded text and unfamiliar names remain challenging.

## Workflow evaluation
`benchmark.py` compares contract and baseline disclosure across all five synthetic tasks. Each fixture verifies entered field values or the required operation before exposing completion. The benchmark's automatic approvals apply only to test fixtures. Results are in `benchmark-results.json`; initial authentication regressions were identified and corrected (numeric-looking random handles and a password-reveal button incorrectly classified as a field). The completed local-driver rerun is summarized below.

The deterministic local driver is not AI. Its success measures workflow/policy integration. Gemini runs and two external-site tasks are recorded separately by `live_check.py`; a planner claiming completion without a verified page result is `needs_review`, not success.

Latest local-driver ablation including bounded action history: 10/10 verified outcomes, with 15,044 bytes of contract-mode planning observations versus 20,106 baseline bytes (25.18% reduction). Context-only bytes were 86 versus 6,305 (98.64% reduction). These are local-driver observation sizes, not cloud request billing sizes. Both modes used the same core privacy enforcement and bounded action history.

Initial live Gemini 3.8 Flash returned HTTP 503; no action executed. Gemini 3.5 Flash-Lite responded, but the initial stateless prompt/schema completed only conference; other tasks hit loops, an invalid action or unverified completion. Those failure records are preserved. The revised agent adds bounded action history, per-observation action variants and explicit executor-owned approval semantics. Live results must be remeasured; local test success does not substitute for this.

## Leakage and attack evidence
Outgoing canaries, URL-encoded/base64 values and misleading `data`/`image_base64` keys are rejected by policy tests. A mock HTTPX receiver confirms the exact inspected and hashed bytes are those handed to transport. This is a bounded transport test, not a network-wide DLP proof. Eight dashboard probes exercise actual local rejection paths. Browser tests check stale pages, unknown targets, duplicate handles, disabled targets, missing OCR and protected-field writes.

The suite does not establish a broad prompt-injection success rate. A malicious authorized website can still mislabel its own fields. No unredacted baseline is sent to a cloud provider. Detection is only part of the boundary; action restrictions and human approvals constrain consequences independently.

## Reproduction and independence
Run `python -m pytest -q`, then start the server and run `benchmark.py` and `evaluate_pixels.py` using `.venv/Scripts/python.exe`. The latter obtains expected regions from annotations only after the detector has processed the screenshot. Browser holdout seeds differ from the 1–5 text corpus. Templates are deliberately small and controlled; layout variations are not independent real-world applications.

For a fair AI ablation, use the same Gemini model, seed, task and core enforcement in both modes. Report request bytes, context bytes, image area, turns and independently verified outcome. A script-only ablation cannot prove that reduced context preserves arbitrary AI reasoning quality.

## Remaining validation
The revised cloud flow most recently received HTTP 402 before producing an action. Its successful end-to-end validation remains open pending project billing/access and a locally entered key. Wikipedia and SauceDemo each succeeded in development, but the last repeated smoke run failed during navigation/capture; the latest JSON preserves those failures. Rerun after relocation before presenting both as reliably passing. The captioned local-driver demo is 143 seconds and does not claim cloud-AI performance.
