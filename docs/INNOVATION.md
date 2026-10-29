# Differentiation and evidence

The organizer's novelty requirement is an acceptance gate, not an extra feature. A detector + redaction + cloud browser-agent wrapper alone would be insufficient. Prior privacy agents already implement local sanitization, placeholders and protected execution; research also covers selective visibility and trust boundaries.

Our defensible pitch is **a task-scoped disclosure contract that makes the agent's privacy decisions inspectable and testable**. Four connected behaviors demonstrate it:

1. Minimal initial observation: semantic controls and status, instead of the entire sanitized document. Compare its actual disclosed bytes against the full sanitized-text baseline.
2. Progressive disclosure: the planner must identify a region; the user reviews and approves a sanitized crop. No silent full-screen fallback.
3. Local secret capabilities: origin, field purpose, task, use count and current observation constrain secret use. Demonstrate a correct fill and rejected cross-field/origin use.
4. Privacy receipts and attack evidence: inspect exact checked payload digests, disclosed regions, policy results and failed probes rather than trust a privacy badge.

These are an original product integration and experimental framing, not claims that capabilities, hashing, redaction or approvals were invented here. Judges decide whether the distinction is meaningful. Do not claim superiority over another system without a matched benchmark.

## Comparison scope
| Approach | Shared foundations | PrivacyLens distinction to demonstrate |
|---|---|---|
| Presidio/Gitleaks/OCR tools | PII and secret discovery | Action and disclosure policy above detection |
| Screenshot redactors | Pixel masking | Task execution, secret permissions, approval and receipts |
| Existing privacy browser agents, including NAYAN | Local sanitization and protected agent workflows | Quantified minimal-context contract plus user-visible region escalation and misuse tests |

## Ablation protocol
Run the same seed, layout and task with contract mode and baseline full sanitized text. Keep detectors, executor, approvals and planner identical. Record text-context bytes, full request bytes, image area released, steps, observed completion and processing latency. Local-driver results prove transport minimization while preserving that scripted workflow; they cannot establish cloud model success. For a real AI comparison, repeat both modes with Gemini using the same model and task settings, then report failures and extra turns.

Future room for innovation: automatically derived purpose contracts with explicit user review, privacy-budget allocation across turns, calibrated sensitivity confidence, formal secret-flow types, signed receipts and per-site semantic attestations. These are future work, not implemented features.
