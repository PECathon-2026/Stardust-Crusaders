# Reuse and original work

Source downloads are under `third_party/`, excluded from our Git history. They are reference checkouts, not copied application code. Runtime packages are installed in `.venv` and `frontend/node_modules`; the project runs without the reference checkouts. Exact inspected revisions are in `upstream-sources.json`; installed versions belong in `requirements.lock.txt` and `frontend/package-lock.json`.

| Upstream | Reused component | License / attribution |
|---|---|---|
| [Presidio](https://github.com/data-privacy-stack/presidio) | AnalyzerEngine/NlpEngineProvider API and recognizers | MIT; package includes license |
| [spaCy](https://github.com/explosion/spaCy) | Local English NER; en_core_web_sm 3.8.0 | MIT; model has its own metadata/license |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | Local ONNX OCR engine and packaged detection/recognition models | Apache-2.0; retain model/package notices |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | CPU inference | MIT |
| [OpenCV Zoo](https://github.com/opencv/opencv_zoo) | YuNet 2023mar face model | YuNet MIT notice copied to `licenses/yunet-MIT.txt` |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Three adapted regexes: github-pat, aws-access-token, gcp-api-key | MIT notice copied to `licenses/gitleaks-MIT.txt`; not the full Gitleaks scanner |
| [Playwright](https://github.com/microsoft/playwright-python) | Chromium automation/screenshot infrastructure | Apache-2.0 |
| React / Vite / TypeScript / Lucide | Dashboard infrastructure and icons | MIT / ISC as recorded in installed packages |
| FastAPI / Pydantic / HTTPX / Uvicorn | API, validation, transport and serving | MIT / BSD notices in installed distributions |
| Pillow / Faker / pytest | Image composition, synthetic fixtures, testing | Respective upstream package notices |

YuNet SHA-256: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`.
Pinned model source: https://media.githubusercontent.com/media/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

Original code: privacy contract and observation format; browser registry/fingerprint; purpose-bound vault; disclosure approvals; action executor checks; exact-payload gate; receipts; dashboard design; synthetic pages; tests; evaluation and documentation. Dependencies are openly attributed; do not present their detectors, browser engine or model inference as our invention.

NAYAN and screenshot-redactor are prior-art references only. No application source or interface is reused. No Browser Use agent loop is forked. No claim of uniqueness follows merely from avoiding copied code.
