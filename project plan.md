# PrivacyLens project scope

## Product
A browser extension that accepts custom prompts on supported websites, screens page data locally, obtains actions from a cloud or local model, and authorizes execution locally. The user stays on the interactive website and can take control at any time.

## Delivery areas
| Area | Implementation |
|---|---|
| Browser experience | Manifest V3 side panel, pairing, same-tab automation, manual takeover |
| Privacy engine | Patterns, local NER, OCR, face detection, selective text and pixel masks |
| Model pathway | Gemini, Groq and Ollama, sanitized observations, exact-byte outbound checks |
| Action authority | Snapshot validation, scoped secret injection, approval, Draft only |
| Demonstration | Five synthetic data categories and supported SauceDemo pages |
| Evidence | Synthetic corpora, policy probes, privacy receipts, reproducible tests |

## Judging checklist
| Criterion | Marks | Demonstration |
|---|---:|---|
| Innovation | 15 | Task-scoped disclosure, scoped secret use and local action authority |
| System design / codebase knowledge | 20 | Trace capture through detection, model transport and execution |
| Problem understanding | 15 | Protect both text and pixels while preserving task controls |
| Test cases | 20 | Positive, negative, stale-page, leakage and approval checks |
| Impact / feasibility | 15 | Working extension, local processing and local AI option |
| Presentation | 15 | Clear 2–3 minute demo with a visible privacy comparison and useful action |

## Submission checks
Rehearse the chosen tasks on a fresh demo page. Keep the local service running, prepare the selected planner, record the extension workflow and explain the privacy receipts. Use the current measured evidence in [evaluation](docs/EVALUATION.md). See [demo script](docs/DEMO.md), [architecture](docs/ARCHITECTURE.md) and [bonus capabilities](docs/BONUS-STATUS.md).
