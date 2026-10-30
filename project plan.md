# PrivacyLens — implementation plan and originality checkpoint

Updated: 30 October 2026. Workspace: `D:\pecathon` (moved from Desktop to free C: storage).

## Implementation revision — 30 October

The user has authorized implementation. Foundation, privacy engine, task contracts, local vault, approvals, Gemini/Ollama adapters, dashboard, fixtures and evaluation tools are implemented. Track actual validation in `docs/phase-status.md` and `docs/EVALUATION.md`; original design targets below are not automatically achieved results.

Concrete implementation changes: React/Vite dashboard + FastAPI; isolated Python 3.11.9; installed Edge in an ephemeral context when bundled Chromium is absent; exact-byte Gemini GenerateContent transport; no provider retries; baseline is full sanitized **text**, not automatic full screenshot transmission; extra sanitized image regions require approval. Local Ollama is an optional uninstalled adapter. Conference uses an AI-generated fictional face fixture and YuNet plus conservative media masks. SauceDemo acceptance stops at a verified cart before checkout. Model output `done` alone is not successful completion.

Phase gates now include: strict policy/browser tests; 50 real screenshots with separate annotations and no vault hints; 50 text cases plus negative controls; both disclosure modes across five verified synthetic workflows; external-site smoke checks; live Gemini validation with a locally entered user key; UI review; evidence documentation and demo recording. Preserve failed targets and limitations in the report. Keep future innovation ideas in `docs/INNOVATION.md` explicitly separate from implemented features.

## 1. Decisions and non-negotiables

- Team: Eshan with Codex; approximately 10 hours available. AI-assisted code generation increases implementation throughput, but integration, measurement and rehearsal still need time.
- Build a local application from reusable components, not a fork of an existing privacy agent.
- Primary reasoning: Gemini over sanitized observations. Local detection and sanitization are mandatory. Local reasoning is optional and must not weaken accuracy or consume required testing time.
- PC inspected: approximately 16 GB RAM, NVIDIA GTX 1650 with 4 GB VRAM, Windows, Node 24 and Python 3.13 installed. Use an isolated Python 3.11 environment for the implementation rather than changing existing installations.
- Cover all five specified scenarios and two external-site tasks: Wikipedia navigation and SauceDemo demonstration checkout.
- Codex downloads repositories, installs dependencies and prepares model assets directly. The user supplies provider credentials locally and reviews demos; no manual repository downloading is required.
- The organizer's latest message makes meaningful originality an eligibility condition. A renamed clone, matching another application's workflow, or merely combining a redactor with a browser agent is not an adequate submission.
- No claim of world-first novelty or universal zero leakage. Distinguish existing techniques, our design contribution and measured outcomes.

## 2. Evaluation rubric and evidence

| Category | Marks | Required project evidence |
|---|---:|---|
| Innovation | 15 | Clear comparison with prior systems, original user workflow, implemented distinctive behavior, ablation showing benefit |
| System design / codebase knowledge | 20 | Trust-boundary diagram, module responsibilities, data contracts, upstream provenance, team walkthrough and design tradeoffs |
| Understanding the problem | 15 | All PS-004 categories/scenarios covered; explain why screenshots, DOM, task instructions, history, metadata and logs all matter |
| Test cases | 20 | Seeded annotated tests, negative cases, fault injection, adversarial pages, actual measurements and reproducible commands |
| Impact / feasibility | 15 | Working local privacy processing on this PC, two external-site tasks, latency/memory results and honest limitations |
| Presentation | 15 | Coherent dashboard, compelling before/after story, live attack blocking, 2–3 minute recorded demo and rehearsal |

The 40 marks for design knowledge and tests require first-class documentation and evidence. The originality rule applies before optimizing this score table.

## 3. Distinctive product concept: a task-bound privacy contract

Proposed contribution: the user sets a privacy contract for a task, the agent operates with only the necessary disclosed context, and every external observation and sensitive action has an inspectable explanation.

This is a design hypothesis. Prior work already covers redaction, placeholders, local reference resolution and guarded actions. The contribution must be demonstrated through the integrated workflow and comparison, not asserted by renaming those mechanisms.

### A. Task-specific disclosure

Select a task profile: checkout, authentication, support, conference, developer settings, or public browsing. Each profile defines allowed public context, protected categories, allowed destinations and sensitive actions.

The default observation contains sanitized semantic controls and minimal task-relevant text. Screenshots are separately sanitized and visible in local preview. Cloud image disclosure is disabled until requested through the contract.

When the planner lacks context, it may request a named region from the current observation. A local policy check may release a sanitized crop, deny the request, or ask the user to approve additional non-sensitive context. The model cannot change the contract or request raw protected values. Persist approved changes only for the current task.

Measure disclosure size, masked area, clarification requests and task completion against a baseline that sends the whole sanitized viewport. Token/image area reduction alone is not proof of reduced reidentification risk.

### B. Expiring secret-use permissions

Store secret values locally. Give the planner opaque references, never values. Bind permission to one task, origin, field purpose, current snapshot and limited use count. An allowed reference cannot be reused in a chat box, URL, search input or changed origin.

Require approval for consequential operations. Display the operation, destination and consequence in the trusted dashboard. Navigation or relevant state changes invalidate pending approvals. This applies least privilege to browser actions; it is not a new cryptographic primitive.

### C. Privacy receipts

Show a local receipt for each attempted model request: contract version, sanitized snapshot ID, disclosed categories/region IDs, redaction counts, detector status, outgoing payload digest, transmission decision and subsequent action result.

Never put raw values, raw URLs, raw screenshots or unkeyed secret hashes into receipts. A payload digest binds the displayed event to bytes; it does not prove correct detection. Call these audit receipts, not certificates of zero leakage.

### D. Live attack lab

Provide controlled attacks such as a webpage requesting a secret in an unrelated field, a stale-action swap, an injected URL destination and a deliberately contaminated outgoing payload. Show which enforcement layer stops each attempt.

Keep the lab separate from ordinary execution. Demo attacks use synthetic values and a local mock receiver. The UI must never manufacture a passing result; it renders test outcomes from actual execution.

## 4. Reuse ledger: take versus build

| Source | Take | Build / adapt | Status |
|---|---|---|---|
| microsoft/playwright (Apache-2.0) | Released Python package, Chromium, locators, screenshots | Collector, opaque IDs, executor and browser tests | Planned dependency |
| data-privacy-stack/presidio (MIT) | Recognizers, including PAN/Aadhaar, anonymization | Browser-context rules, detector fusion, semantic placeholders | Local source download initiated |
| explosion/spaCy | Packaged local English NLP/model | Domain-sensitive container policies | Planned dependency; preserve model terms |
| gitleaks/gitleaks (MIT) | Selected secret pattern definitions | Python recognizers and compatibility tests; no remote verification | Local source download initiated |
| RapidAI/RapidOCR (Apache-2.0) | OCR package and ONNX model inference | Text-to-mask mapping and screenshot checks | Local source download initiated |
| opencv/opencv_zoo YuNet directory (MIT) | Face model and documented inference interface | Face/tile masking and failure handling | Source download initiated; LFS model binaries need explicit retrieval |
| python-pillow/Pillow (MIT-CMU) | Pixel operations and fresh PNG encoding | Opaque compositor and coverage assertions | Planned dependency |
| FastAPI, Pydantic, HTTPX | Local HTTP API, validation, transport | Contract engine, run management, receipts and outbound gate | Planned dependencies |
| React, Vite | UI runtime/build tooling | Original privacy-contract dashboard, disclosure review and attack lab | Planned dependencies |
| Faker, pytest | Synthetic generation and test framework | Ground truth, scenario fixtures, metrics and adversarial harness | Planned dependencies |
| Ollama + Qwen3 4B | Optional quantized local inference | Same planner interface and comparative checks | Conditional bonus |
| Rohinth-S/NAYAN | Prior-art inspection only | No application code copied, no fork or UI reuse | Local reference download initiated; excluded from runtime/submission |
| cleanroom-ai/screenshot-redactor | Prior-art inspection only | No application copy | Research only |

Use package releases for runtime dependencies rather than importing entire cloned repositories. Keep inspected source in ignored `third_party/`. Record exact commits, package versions, model hashes, copied rule IDs and applicable license notices. Exclude reference checkouts from the submitted source archive; retain necessary attribution for actual dependencies/adaptations.

Do not copy NAYAN's prompts, UI, protocol implementation, tests or documentation. Consult it only to understand the comparison baseline. A new name or frontend alone is not innovation.

## 5. Architecture and contracts

Local Chromium → capture → structural/text/OCR/face detection → task-contract filter → sanitized observation → final serialized-payload gate → Gemini → proposed action → policy/approval → local executor.

Raw page data and secret mappings remain local. The model sees only allowed sanitized information and has no general browser, shell, filesystem or arbitrary network tools.

Logical modules: browser adapter; detectors; sanitization; contract policy; disclosure controller; secret permissions; provider gateway; action executor; receipt recorder; dashboard; evaluation harness.

Important shared types:

- `TaskContract`: task profile, allowed origins, protected categories, allowed disclosure regions, action permissions and revision.
- `SanitizedObservation`: snapshot identity, opaque page alias, safe controls/text, available region references and approved sanitized images.
- `Finding`: category, local source span/box, detector and reason. Raw matched values remain in local detector state.
- `ProposedAction`: action type, snapshot and opaque target/reference; strict type-specific fields.
- `DisclosureRequest`: current snapshot, existing region ID and requested context purpose. No raw selectors or arbitrary coordinates.
- `SecretPermit`: local-only binding of task, origin, field purpose, snapshot and remaining uses.
- `PrivacyReceipt`: sanitized metadata, transmitted-byte digest and enforcement outcomes.

Backend interfaces support run creation/status/stop, local secret entry, preview, disclosure decisions, action approval, receipts and evaluation export. Serve dashboard/API on one loopback origin; test pages use a different origin. Use per-launch authentication and origin checks so controlled webpages cannot invoke the trusted control API.

### Capture and detection

Collect visible text, control roles/labels/states and rectangles. Sanitize retained titles, accessible names and attributes. Exclude cookies, storage, raw HTML and hidden values. Ground truth stays in test-only sidecars and is never available to the detector.

Recognize IDs, cards, email/phones, passwords/OTPs, keys/tokens/IPs, names/addresses, private messages, medical information and faces. Context-based protection overrides an invalid checksum in a known sensitive field. Merge overlapping spans while preserving useful public labels.

Use a fixed viewport initially. Detect navigation/layout changes; invalidate stale observations and approvals. Inspect supported frames/shadow roots; mask unsupported surfaces conservatively and disclose limitations.

### Sanitization and transmission

Create opaque masks from DOM ranges, OCR and face findings. Run pixel detection against the exact image being sanitized; fresh PNG encoding drops copied metadata. No blur-based guarantees. Private image buffers must never briefly expose raw pixels in exported surfaces.

Apply one gate to every model request, including retries, history and disclosure requests. Validate exact serialized bytes, permitted destination and image provenance. Search known synthetic/secret values and supported normalized encodings; residual OCR is an additional check, not proof of absence.

Any required detector/validation failure blocks the request. Retry unstable capture once, then stop the step. Never fall back to raw observations.

Use Gemini `gemini-3.8-flash`, subject to a harmless account-access check. Use a single HTTPX adapter and structured responses; set Interactions `store=false`, keep sanitized history locally, and disable server-side tools and continuation. Provider processing terms remain separate from application retention.

### Execution and approvals

Allow click, public fill, secret fill, select, scroll, wait, context request and done. No model JavaScript, CSS/XPath, arbitrary URLs or ungrounded coordinates. Verify target, role, visibility, origin, snapshot and task permissions before execution.

Secret fill resolves locally with field-bound permission and returns status only. Require explicit approval for purchases, sending messages, deletion and security/credential changes. Revalidate after approval. Runs have bounded steps/time and at most one retry for transient model errors; no automatic retry of consequential actions.

### Retention and boundaries

One active run, in-memory state, ephemeral browser context, raw previews local only, no automatic trace/video/request-body logs. Persist aggregate sanitized evaluation and receipts only on export. Stop clears session references and closes the context; do not claim guaranteed erasure from garbage-collected memory.

This boundary protects this application's model pathway. It does not prevent a destination website receiving an authorized form value, other software capturing the screen, or a compromised operating system reading memory.

## 6. Implementation phases and checkpoints

Progress updates at each checkpoint summarize working behavior, tests, remaining risk and the next phase. Ask the user only for consequential product choices, missing credentials or a change to agreed scope. Routine fixes and repository downloads are autonomous.

| Phase | Work | Evidence / checkpoint |
|---|---|---|
| 0 — Originality and provenance | Save plan/research, obtain upstream sources, compare prior art, establish attribution ledger and distinctive workflow | Reviewable originality statement; no existing application copied |
| 1 — Foundation | Isolated environment, package/model setup, local API/UI shell, strict contracts, Chromium and harmless Gemini smoke test | One-command start; dependency checks; secrets excluded from source control |
| 2 — Privacy engine | Structural rules, PII/secrets, OCR/faces, placeholders, screenshot masks, before/after preview | Five scenario previews; annotated detections; failures block output |
| 3 — Safe agent | Gemini adapter, outgoing gate, grounded executor, local secret permissions, approvals and Stop | Complete task with no raw secret sent; wrong-field secret attempt blocked |
| 4 — Differentiating workflow | Task contracts, progressive sanitized disclosure, privacy receipts and attack lab | Side-by-side baseline comparison and real enforcement receipts |
| 5 — External feasibility | Wikipedia navigation and SauceDemo demo credentials/cart/checkout review | Two recorded external-site attempts with honest results |
| 6 — Evaluation and hardening | Held-out cases, negative cases, attacks, faults, transport inspection, latency/memory and ablation | Reproducible metrics and regression results |
| 7 — Documentation and presentation | Architecture/code walkthrough, setup, attribution, limitations, demo script/video and fresh-start rehearsal | Submission-ready project and explainable codebase |

Indicative budget: phases 0–1: 1 hour; phase 2: 2 hours; phase 3: 1.5 hours; phase 4: 1.5 hours; phase 5: 0.5 hour; phase 6: 2 hours; phase 7: 1.5 hours. This is a prioritization guide, not a restriction based on typing speed.

After hour 8, prioritize correctness, reproducibility and presentation. Preserve meaningful differentiation; if necessary reduce animations, optional local inference and nonessential polish. Never remove privacy gates or substitute scripted playback for claimed agent success.

Optional local mode: try Ollama Qwen3 4B only after core acceptance passes and without taking the final testing/rehearsal reserve. Cap setup/benchmark work at 20 minutes. Keep it only if smoke tasks and policy tests pass without instability and warm median action latency is at most 10 seconds. No silent cloud fallback in local mode.

## 7. Test strategy and evaluation scenarios

Required scenarios: (1) checkout with card/address/CVV, (2) authentication with email/password/OTP, (3) support with phone/private messages, (4) conference with fictional face fixtures and participant labels, (5) developer settings with keys/tokens/IPs. Include successful actions and approvals, not just detection screenshots.

External tasks: Wikipedia article search/section navigation; SauceDemo public demo login via local secrets, product selection/cart and checkout review. No personal accounts or actual purchase.

Start with 50 annotated privacy cases: five scenarios × two layouts × five seeded variants. Hold out one layout per scenario. Add ten agent tasks, repeated twice where API budget allows; twenty attacks/faults; and two live-site checks. Increase meaningful coverage if time permits rather than generating redundant tests.

Negative cases include ordinary totals/order IDs, public documentation containing example tokens, benign instructions and non-sensitive text adjacent to PII. Edge cases include split DOM text, Unicode separators, partial fields, reveal toggles, small OCR text, zoom/scroll, unsupported frames, detector timeout, stale targets, forged approvals, wrong-field secret reuse and contaminated metadata/history.

Inspect exact application HTTP transport requests and a local mock receiver. Browser request monitoring alone does not cover Python model-client traffic. The mock receives synthetic data only. Never run an unredacted comparison against a real cloud provider.

For innovation ablation, compare the same tasks under: A) full sanitized viewport and ordinary placeholders; B) task contracts, progressive disclosure and scoped secret permissions. Measure useful context retained, bytes/image area disclosed, task success, extra turns and prevented misuse. Keep core privacy checks enabled in both; any deliberately unsafe baseline belongs in an isolated synthetic mock test.

Targets, not claimed results: recall ≥95%; entity precision ≥90%; fixed non-sensitive UI QA ≥90%; task success ≥80%; all five smoke scenarios; zero observed leakage in tested paths; all specified fail-closed and permission tests pass. Report per-category recall, excess masked pixels, request/value leakage denominators, p50/p95 latency, cold/warm behavior, memory and model/API usage. Warm privacy-processing p95 target: under three seconds on this PC.

Do not conceal failed targets. Report unsupported surfaces and uncertainty. A passing known-canary check is not evidence that unknown PII can never leak.

## 8. Documentation and presentation deliverables

- README: purpose, launch, configuration, demo, test commands, actual completion status.
- Architecture/data-flow guide: trust boundary, module responsibilities, contracts, failure paths and threat model.
- Reuse/provenance inventory: exact sources, licenses, adapted rule IDs, commits and model checksums.
- Innovation comparison: baseline similarities, our integration differences, ablation results and limitations.
- Evaluation report: corpus, split, annotations, environment, actual results and reproduction.
- Codebase walkthrough: explain each module, why chosen, likely judge questions and tradeoffs.
- Demo script and 2–3 minute video: task contract → redaction → permitted action → malicious request blocked → inspectable receipt → measured results.

Current implementation status must be tracked honestly in `docs/phase-status.md`. Repository download is preparation, not proof of a working system.

## Sources

- Full initial research: `docs/research.md`.
- Gemini model: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- Gemini storage behavior: https://ai.google.dev/gemini-api/docs/interactions-overview
- Source-linked privacy references: https://arxiv.org/abs/2610.16778
- Available-but-invisible prior work: https://arxiv.org/abs/2602.10139
- NAYAN prior application: https://github.com/Rohinth-S/NAYAN
- Screenshot Redactor prior application: https://github.com/cleanroom-ai/screenshot-redactor

Novelty comparison remains a required phase-0 check; these sources establish that several underlying mechanisms already exist.

## Live provider follow-up
Groq is the working text-only cloud alternative. The schema compatibility fix is verified by completed checkout and sign-in tasks. Next: resolve support action repetition and category selection, pace free-tier requests, validate support/conference/developer, then update the final presentation with measured cloud results. Keep local screenshot protection active; Groq text planning does not receive pixels.

## Eshan reliability-stage checkpoint
Implemented sanitized select-option/current-selection context, form-error feedback, a repeated-action guard, and cancellable Groq pacing. Local automated and deterministic scenario checks pass. Next gate: user tests STAGE-TESTING.md and live Groq support/conference/developer regression after re-entering the session key. Give the user a feature checklist at every subsequent stage boundary.
## Prompt experience checkpoint
The primary route now offers a prompt sidebar beside a protected browser preview; Privacy Lab is separate at `/lab`. User instructions and one of seven exact supported addresses enter the existing privacy/automation engine. Unsupported URLs are rejected server-side. This initial product stage is a controlled-browser web workspace, not a browser extension or general existing-tab agent.

Acceptance checks cover prompt submission, settings, approvals, Stop, protected/original preview, URL rejection, Privacy Lab navigation and mobile layout. A live conference task also passed through the prompt UI. Groq success evidence exists across all five synthetic scenarios across separate attempts/revisions, with failures retained. Support required prompt rephrasing after a contextual NER false positive. Next: user acceptance and an updated presentation/demo showing the prompt interface and measured limitations; broader website/extension support requires separate implementation and evaluation.


## Required next product stage: actual browser side panel
User clarified that a screenshot workspace is not the intended product. Implement a genuine browser extension side panel attached to the selected real tab, reusing the local privacy service and validated action policy. Acceptance must include ordinary website interaction, explicit agent/manual handoff, preserved same-tab login state, prompts and approvals in the panel, and Privacy Lab as optional evidence tooling. Do not claim this stage is implemented by merely opening a separate browser window.

Credential UX: user logs in directly using the browser or explicitly enters a secret in local panel settings. Do not extract the laptop password database. Browser/password-manager autofill remains a user-controlled browser feature, not a model tool. Model-facing observations disclose only sanitized fields/state or scoped secret references. The existing implementation still uses synthetic presets/local overrides and has no extension or manual pause/resume yet.


## Genuine extension checkpoint — Eshan, 30 October 2026
The actual Manifest V3 side panel is implemented and tested beside a real interactive tab. Pairing, same-tab browser control, local provider settings, prompts, approvals, Take control, preserved tab/session, local privacy preview and request receipts are available. The explicit Private/Public toggle replaces the proposed automatic classification; Private is the default. Recognized identifiers, local secrets and private regions remain protected in Public mode. Added synthetic Aadhaar/PAN and medical-record examples and bounded recapture for pages changing during capture.

Validation: 108 automated tests passed. Installed-extension integration verified manual prefilled sign-in, session retention, pause/edit, inspection and Stop using the local driver. Live Gemini through the actual side panel completed the conference mute task in two observations with HTTP 200 and no image disclosure. Evidence is in live-extension-gemini-conference-results.json. Expanded screenshot corpus: 160/160 annotated text regions, 50 screenshots, median 2419.5 ms, p95 3013 ms (still above the 3-second target).

User acceptance instructions: docs/EXTENSION-TESTING.md (or EXTENSION-TESTING.md from this docs directory). Supported targets remain five local demos and SauceDemo; Wikipedia is unchanged in the earlier workspace. Remaining phase: live extension validation of sign-in, checkout approval/denial, support, developer and SauceDemo; user acceptance; presentation refresh. Arbitrary-site access and universal detection accuracy are not claimed. Earlier entries are historical milestones superseded by this checkpoint.


## Laksh handoff — custom prompts and extension-only entry
Laksh resumed ownership on the shared laptop. Removed the old screenshot-agent UI; the home page now explains extension setup and links to the evidence lab. Custom extension prompts reach the LLM and no longer auto-finish just because a preset fixture outcome exists. Only the exact canonical example (or local test driver) uses preset outcome verification; other tasks finish as planner-finished / needs-review. This avoids claiming automatic correctness for an arbitrary request. The support fixture accepts nonempty replies and either supported category instead of hard-coding one message.

Saved-browser-password and autofill-data extraction is explicitly out of scope at the user's request. Manual login and explicit local secret injection remain. Reference clones are optional, but installed dependencies, model assets, licenses and provenance must stay. No reference folders were deleted in this checkpoint.

Time-critical next work: validate a custom prompt, demonstrate denied approval and blocked unsafe payload, record the required 2–3 minute video, and rehearse the architecture/limitations explanation. General arbitrary-site control is a future phase, not required by PS-004's controlled-page evaluation scenarios.


## Laksh: task-authority restriction and bonus audit
User confirmed the reported send followed clicking Approve; the approval gate did not silently bypass consent. Added explicit per-run Draft only enforcement plus a conservative English negative-instruction trigger. Consequential recognized clicks are blocked before approval/execution. See docs/BONUS-STATUS.md for honest bonus coverage, innovation candidates and remaining required demonstration work. Saved-browser-data extraction remains excluded. Unused reference checkout removal was blocked by automatic review; the folders remain. Attribution is retained.
