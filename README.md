# PrivacyLens — Stardust Crusaders

**Permission to do more. Access to less.** A local browser-agent workspace with task-scoped disclosure, local secret capabilities, consequential-action approval and inspectable privacy receipts.

## Run on Windows

```powershell
cd "D:\pecathon"
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```
Setup is needed once; start is used thereafter. Open http://127.0.0.1:8765. Fixtures run on 8766. Requires Node/npm, Python with pip, internet for initial dependency/model downloads and roughly 16 GB RAM. Python 3.11.9 is isolated. An ephemeral Microsoft Edge session is used if Playwright Chromium is absent; it never attaches to your normal browser profile.

Wait for “Local protection ready”. Choose a scenario and Start protected task. Inspect original/sanitized views locally; approve consequential actions when prompted. Stop & clear closes the controlled browser and clears run secrets/previews.

### Planner choices
- **Local test driver:** deterministic fixture walkthrough, no AI call or key. Exercises the real privacy pipeline; not an AI success benchmark.
- **Groq:** add a Groq key in local Settings and select Groq for sanitized text planning with `openai/gpt-oss-120b`. Keys stay in memory until restart. Local screenshot masking still runs, but this planner cannot receive images. Free accounts have rate limits. See [Groq setup and validation](docs/GROQ.md).
- **Gemini:** add a key in local Settings, select a supported model, then select Gemini. Keys stay in backend memory until the process ends. Exact request bytes pass the local gate. Provider data-handling terms still apply.
- **Ollama:** optional adapter to an existing local instance at `127.0.0.1:11434`, model `qwen3:4b`. Text only, no cloud fallback. Not installed by setup; evaluate separately on this laptop.

Five synthetic profiles cover checkout, authentication, support, conference and developer settings. Two external presets target Wikipedia and SauceDemo. Use demonstration credentials and synthetic data for judging.

## Reproduce verification
```powershell
.\.venv\Scripts\python.exe -m pytest -q
# Keep start.ps1 running for the following:
.\.venv\Scripts\python.exe benchmark.py
.\.venv\Scripts\python.exe evaluate_pixels.py
.\.venv\Scripts\python.exe verify_external.py
# Once a key is saved locally:
.\.venv\Scripts\python.exe live_check.py gemini
# Captioned synthetic local-driver video (app must be idle):
.\.venv\Scripts\python.exe record_demo.py
```
The benchmark automatically approves synthetic test tasks, compares both disclosure modes and saves evidence under `docs/`. Screenshot evaluation uses separate annotations without supplying known secrets to the detector. The dashboard’s text evaluation is a smaller, separately labeled corpus.

Read [project plan.md](project%20plan.md) for the agreed scope, source reuse, phases, test targets and judging rubric. Read [docs/research.md](docs/research.md) for the upstream survey.

Source checkouts in `third_party/` are ignored reference/dependency material, not application implementation. NAYAN is prior art only and must not be copied into the application or submission.

## Documentation and scope
Read [architecture](docs/ARCHITECTURE.md), [innovation](docs/INNOVATION.md), [reuse/licenses](docs/THIRD_PARTY.md), [phase status](docs/phase-status.md), [demo guide](docs/DEMO.md) and [synthetic asset](docs/ASSETS.md).

Protection applies to application-controlled model requests and execution. Websites still receive values deliberately entered into their forms. Detection can miss unknown PII; conservative masking can lose context. Hashes are not proofs of perfect redaction. Original pixels exist in local memory/preview. Do not claim production security or AI performance from scripted tests. Consult the evaluation report for actual results and unmet targets.

Credentials must be configured locally and never committed. Reference checkouts, virtual environments, raw previews and runtime state are not submission source files.

Development is AI-assisted with Codex. Open-source components are credited separately from the application integration. See `CONTRIBUTING.md` for the checkpoint and attribution workflow.
