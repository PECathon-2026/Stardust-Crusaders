# Bonus status and remaining submission work

Status on 30 October 2026. These are implementation claims with bounded evidence, not a claim of all bonuses completed.

| PS-004 bonus | Status | Evidence or remaining work |
|---|---|---|
| Fully local AI | Adapter only | Ollama adapter exists, but a local model and end-to-end local AI run are not validated. The deterministic test driver is not AI. |
| Advanced contextual PII | Partial | Presidio/NER, OCR, face detection and DOM private-region hints. Unknown PII and false positives remain. |
| Adaptive context preservation | Partial | Span-level masking, task-minimal observations, explicit public/private profiles and approved sanitized-region disclosure. No calibrated automatic public/private classifier. |
| Prompt injection/adversarial pages | Partial | Model action schema, local validation, leak gate, stale-page checks and misuse probes. Eight local probes are not an end-to-end prompt-injection benchmark. |
| User-defined privacy rules/explanations | Partial | Private/public choice, explicit Draft only action restriction, fixed redaction categories/reasons. Arbitrary user-defined PII patterns are not implemented. |
| Local secret injection | Implemented, bounded | Origin/field/task-scoped memory-only values, limited uses, model sees references. No password-store extraction. |
| Automated synthetic leakage testing | Implemented, bounded | Known synthetic values/canaries and outgoing-payload tests. Does not establish universal zero leakage. |
| Cross-browser/desktop agents | Not validated | Real Chrome for Testing extension verified. Edge compatibility and general desktop operation are not verified. |
| Human approval | Implemented | Consequential recognized controls and sanitized image-region disclosure need approval. |

## New distinction: locally enforced draft authority
A task can carry an explicit Draft only restriction. Common English phrases such as "do not send" also enable it conservatively; the switch is the dependable user control for other wording/languages. It is bound to one run and shown in activity. The executor rejects recognized consequential clicks before asking for approval, even when the planner proposes them. A new run is required to lift the restriction. The current rule uses known control labels, so it is not universal semantic understanding of every website. Scope remains supported demo pages and SauceDemo.

Present this together with scoped secret use, minimal context, approved region disclosure and receipts. The innovation claim is the integrated, demonstrable control over what the AI can see and do, not invention of redaction or hashing.

## Core items before more bonuses
1. Repeat the exact custom draft task in the real extension and inspect the actual fields and absence of submission.
2. Demonstrate denied approval and a detected unsafe outgoing payload being blocked.
3. Record the required 2–3 minute video with actual extension flow, before/after preview, AI action and a blocked unsafe request. The older local-driver video does not fully represent the current product.
4. Preserve setup instructions, architecture, detection methodology, action validation, trust limits, reproducible scripts/results and dependency attribution.
5. Rehearse the limits: supported sites/actions only; per-scenario reliability still incomplete; screenshot p95 slightly exceeds 3 seconds; synthetic accuracy is not universal.

## Next innovation candidates, not implemented
- A user-visible per-task disclosure budget, enforced before each model request.
- Synthetic webpage prompt-injection challenges evaluated separately from simple policy-unit probes.
- A plain-language end-of-task receipt connecting requested task, denied actions and information disclosed.

Do not add every bonus at the expense of the required demo and reliable privacy boundary.
