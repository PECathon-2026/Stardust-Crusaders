# PrivacyLens — Stardust Crusaders

PrivacyLens is a Chrome side-panel AI agent with local privacy screening. Type a task beside the real webpage, inspect what the model can see, and approve sensitive actions before execution.

## Start on Windows
```powershell
cd D:\pecathon
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```
Run setup once. Keep the server running, then launch the extension in another terminal:
```powershell
powershell -ExecutionPolicy Bypass -File .\launch-extension.ps1
```
The launcher installs its browser if needed and opens Chrome for Testing with PrivacyLens. Open the connection page from the side panel, enter its session code and connect. Open a demo website from the panel, enter a task and choose a planner. See [extension setup](docs/EXTENSION.md).

The local app uses port 8765 and synthetic demo pages use 8766. The home page provides setup links. Privacy Lab at `/lab` provides evaluation and evidence tools. Initial setup requires Python, Node/npm and internet access for dependencies and model assets.

## Features
- Same-tab automation with custom prompts, manual takeover and approval controls.
- Local pattern, NER, OCR and face detection with selective text and pixel masking.
- Private/Public profiles, task-minimal context and approved sanitized image regions.
- Local secret injection bound to task, origin, field purpose and limited uses.
- Draft only blocks recognized consequential actions before approval.
- Checked outbound payloads and inspectable privacy receipts.

## Planner choices
| Planner | Configuration |
|---|---|
| Gemini | Save a provider key in panel Settings. Supports sanitized text and approved image regions. |
| Groq | Save a Groq key. Text planning with `openai/gpt-oss-120b`. See [Groq](docs/GROQ.md). |
| Ollama | Run `qwen3:4b` locally at `127.0.0.1:11434`. Text planning without a cloud fallback. |
| Local test driver | Deterministic fixture checks without an AI model or key. |

For Ollama, install Ollama separately, run `ollama pull qwen3:4b`, ensure the local service is running and select Ollama in the panel. The team has successfully tested local AI on its device. Setup does not install the language model.

Provider keys and explicit local secrets remain in server memory and clear on restart. No `.env` file is needed. Never paste secrets into task prompts or commit them.

## Demo and testing
Supported extension targets are five synthetic categories (checkout, identity/sign-in, support/health, meeting and developer settings) and SauceDemo login/inventory/cart pages. Use synthetic data for demonstrations.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
# With the local server running:
.\.venv\Scripts\python.exe verify_identity_images.py
.\.venv\Scripts\python.exe benchmark.py
.\.venv\Scripts\python.exe evaluate_pixels.py
```
The benchmark automatically approves synthetic fixture operations. Run it while the app is idle. It measures the deterministic workflow; live AI and detection evidence have separate scopes.

## Documentation
- [Architecture and code map](docs/ARCHITECTURE.md)
- [Hands-on tests](docs/EXTENSION-TESTING.md)
- [Demo and voice-over script](docs/DEMO.md)
- [Sensitive-data demo map](docs/DEMO-DATA-MAP.md)
- [Bonus capabilities](docs/BONUS-STATUS.md)
- [Evaluation](docs/EVALUATION.md)
- [Original contribution](docs/INNOVATION.md)
- [Dependencies and licenses](docs/THIRD_PARTY.md)
- [Synthetic assets](docs/ASSETS.md)
- [Project scope and judging checklist](project%20plan.md)

## Privacy boundary
Raw page data is processed locally. The model receives screened context; authorized form entry still sends values to the website. Detection can miss unknown sensitive information or over-mask useful content. Receipts identify checked payloads, not proofs of perfect privacy. The extension controls supported tabs and does not read the browser password database.
