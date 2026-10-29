# Prompt-first judging demo

Goal: demonstrate useful AI browser automation and prove the privacy boundary with inspectable evidence. A familiar website is useful for credibility, but controlled synthetic pages are explicitly required by PS-004 and make sensitive-data tests reproducible.

## Suggested 2–3 minute sequence

1. **Prompt and task (0:00–0:40).** Type a task in the Browser Agent. Wikipedia live AI validation passed (143.28 seconds); SauceDemo also passed (122.14 seconds). Use Wikipedia for recognition or SauceDemo for demonstration login/cart automation. A public Wikipedia page alone does not demonstrate meaningful private-data protection. Never place a real order.
2. **Privacy demonstration (0:40–1:20).** Use the synthetic checkout/authentication page: show the local original and protected view, explain typed redaction placeholders and locally injected secrets. Distinguish what the website receives from what the AI receives. Groq gets sanitized text, not these screenshot pixels.
3. **Human control (1:20–1:40).** Show approval before the synthetic consequential action. Decline once if time permits, demonstrating that execution stops.
4. **Unsafe request blocked (1:40–2:05).** Run a canary leakage/security probe in Privacy Lab. Explain that the application blocks detected unredacted data before transport. This is controlled evidence, not a universal security claim.
5. **Evidence and originality (2:05–2:40).** Show a payload receipt, scoped secret capability and task-bound/full-sanitized-text comparison. Present measured detection precision/recall and known limitations. Label local-driver vs live-AI results separately.

Free-tier pacing makes a fully live three-minute run unpredictable. Use a short live task plus clearly labeled recorded results for longer runs. The delivered video must be updated to show the prompt UI and live-AI evidence; the existing local-driver video is not proof of AI performance.

Live external evidence is saved in `live-groq-wikipedia-saucedemo-results.json`; both are single successful attempts. SauceDemo is a public test store, not a real retailer.

## PS-004 alignment

- Detection: patterns, validation, DOM structure, Presidio NER, OCR and face detection.
- Sanitization: semantic text placeholders and opaque screenshot masks; local original/protected preview.
- AI/actions: actual cloud reasoning over sanitized text, local secret injection, validated targets, human approvals.
- Validation: outgoing gate, fail-closed paths, canary tests, action/permission tests and bounded privacy receipts.
- Evaluation: all five synthetic categories implemented; successes and failures recorded across live AI attempts; no claim of consecutive 5/5 reliability.
- Deliverables: code, setup, architecture, tests and measured reports exist. Updated prompt-first video and final demo rehearsal remain.

## Bonus points and honest status

| Bonus | Current position |
|---|---|
| Contextual PII detection | Implemented NER/OCR/face + DOM/context policies; false positives and conservative masking documented |
| Adaptive redaction/context preservation | Task-bound context and sanitized-region disclosure workflow implemented; region-image path is Gemini-specific, not demonstrated through text-only Groq |
| Injection/adversarial protection | Layered local restrictions and controlled probes implemented; not a broad prompt-injection benchmark |
| User-defined privacy rules and explainability | Findings/reasons exist; a general user-editable rules interface is not built |
| Local secret injection | Implemented with task/origin/field/use limits |
| Automated canary leakage testing | Implemented |
| Cross-browser/desktop support | Controlled Chromium/Edge pathway; broad cross-browser/desktop validation not established |
| Human approval | Implemented and tested |
| Fully local AI | Ollama adapter exists; no validated local-model demo yet. Deterministic local driver does not qualify as local AI |

Novelty pitch: task-scoped disclosure, local secret permissions and auditable receipts, with a measured minimal-context comparison. Do not pitch ordinary browser automation or masking alone as novel, or claim the underlying mechanisms were invented by the team.
