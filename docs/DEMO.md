# 2–3 minute demonstration and judging guide

Before recording: run setup/start, wait for detector readiness, open the dashboard, keep screen at 1440×1000 if possible. Use only synthetic fixtures. If using Gemini, enter a key in local Settings and select the cloud planner; otherwise explicitly say the demonstration uses the deterministic local test driver. Do not show a key entry or any real account.

## Script
**0:00–0:20 — Problem and novelty.** “A browser agent can see far more than its task requires. PrivacyLens turns a task into a disclosure contract: the agent receives enough context to act, while local policy controls secrets, extra visibility and consequential actions.”

**0:20–1:05 — Checkout.** Start the checkout. Switch between original and sanitized local previews. Point out the protected name, address, card and fields. Explain that the model gets reference names rather than secret values. At Place demo order, show the approval pause; approve once and show the verified outcome. With the local driver, say it validates the pipeline rather than AI reasoning.

**1:05–1:30 — Misuse resistance.** Open Attack lab, run probes, show actual results. Explain wrong-origin and wrong-field secret rejection. Be precise: these are local enforcement probes, not a comprehensive prompt-injection benchmark.

**1:30–2:00 — Original workflow.** Show Privacy contract and Evidence. Explain minimal context, approved region requests, and exact-payload receipts. Show the measured full-text versus minimal-context comparison from `docs/benchmark-results.json` once generated. Do not invent AI success numbers.

**2:00–2:30 — Proof and boundaries.** Show tests/results and one conference/developer scenario. State the limitations: detectors can miss unknown PII, approved sites receive submitted values, and receipts are audit records rather than formal proofs. Reused detectors are openly attributed; the integration and enforcement workflow are original.

## Rubric mapping
| Criterion | Marks | Demonstrate |
|---|---:|---|
| Innovation | 15 | Contract/disclosure/capability workflow and measured ablation; acknowledge prior art |
| System design / codebase knowledge | 20 | Trace capture → sanitized observation → exact-byte gate → planner → policy → execution; explain every module |
| Problem understanding | 15 | Both text and pixels, five scenario types, local raw data, usefulness retained |
| Test cases | 20 | Policy, API, browser staleness, image masking, detector corpus, real scenario completion and failed cases |
| Impact / feasibility | 15 | Runs on this laptop; measured latency; explicit cloud/local boundaries and practical limits |
| Presentation | 15 | Clear live task, visible approval, attack evidence, honest reproducible results |

## Questions to rehearse
- Why are regexes insufficient? Contextual names and pixel text need other detectors; generic classifiers can also miss things.
- Why opaque masks? Blur is not reliable removal; rebuilt solid pixels eliminate the covered original region.
- How does the agent fill a password it cannot see? It proposes a scoped reference; local code validates origin, field, snapshot and use count before resolving it.
- What if a page tells it to ignore instructions? Page text is untrusted, but prompt wording is not the main defense: strict actions and local permissions constrain execution.
- Does zero observed leakage prove privacy? No. State tested denominators and attack scope.
- What did you copy? Infrastructure libraries and three attributed patterns; no prior privacy-agent application fork.
- What is incomplete? Consult the current phase-status and evaluation report; distinguish adapter implementation from live-provider validation.

Record a screen demonstration after rehearsing. A recorded local-driver demo must be labeled as such. Do not present synthetic page success as performance on arbitrary websites.
