# Evaluation and reproducibility

Results refer to their saved test inputs and revisions. Synthetic coverage does not establish universal detection accuracy or arbitrary-site reliability.

## Evidence index
| Check | Recorded evidence | Interpretation |
|---|---|---|
| Text detection | 110 entities across 50 cases and 4 negative controls; 100% recall, about 98.2% precision | Two false positives in the synthetic corpus. Text latency excludes browser capture, OCR and AI. |
| Identity images | `identity-image-results.json` | OCR identifier and explicit private-portrait coverage across two widths and two layouts. Independent annotations; no known-value hints for identifier detection. |
| Screenshot corpus | `pixel-results.json` | 50 screenshots and 160 annotated text regions in the recorded fixture revision; median 2419.5 ms, p95 3013 ms. This predates image-card additions and is not a benchmark of the current card assets. |
| Disclosure comparison | `benchmark-results.json` | Ten verified deterministic workflow outcomes; task-bound observation bytes reduced 25.18%. This is not an AI-quality benchmark. |
| Real extension + Gemini | `live-extension-gemini-conference-results.json` | Meeting mute verified through the actual side panel and attached tab in two observations. |
| Local AI | Team acceptance test, 30 October 2026 | Team confirmed Ollama works locally. No automated timing/reliability report is attached to that manual test. |

Automated test checkpoints include a full run of 109 passing tests and a later focused run of 37 browser/extension tests. They are separate runs, not an additive count. Re-run the suite to report the result for a new checkout.

Groq records include verified checkout, authentication, support, meeting and developer outcomes in `live-groq-results.json`, `live-groq-support-results.json` and `live-groq-followup-results.json`. These are selected attempts across revisions, not a consecutive five-task trial. Saved reports retain failed attempts and their provider/policy outcomes.

## Security checks
Tests cover encoded canaries, misleading payload fields, exact checked/transmitted bytes, secret scopes, disabled/unknown targets, stale pages, denied approvals and approved-only image disclosure. Attack Lab executes local rejection probes. It is not a comprehensive end-to-end prompt-injection benchmark.

## Run the checks
```powershell
.\.venv\Scripts\python.exe -m pytest -q
# Start the server and leave it idle for the following:
.\.venv\Scripts\python.exe verify_identity_images.py
.\.venv\Scripts\python.exe benchmark.py
.\.venv\Scripts\python.exe evaluate_pixels.py
```
Pixel evaluation reads expected annotations separately from detector inputs. Use [extension acceptance tests](EXTENSION-TESTING.md) for the interactive workflow. Provider timing includes inference and quota pacing, while text-only detector timing does not. The recorded screenshot p95 slightly exceeds the three-second target.
