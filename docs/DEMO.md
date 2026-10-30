# Demo and voice-over guide

Use the actual Chrome side panel beside the website. Prepare a connected local service and a working planner before recording. Keep provider Settings and real accounts off screen. All examples below use synthetic data.

## Suggested 2–3 minute sequence
| Time | Screen action | Voice-over |
|---|---|---|
| 0:00–0:20 | Show the identity demo beside the extension. | “PrivacyLens is an AI browser agent that works beside the website. Our focus is controlling what the model can see and what it is allowed to do.” |
| 0:20–0:55 | Open Privacy, inspect locally, compare protected and local-original previews. | “This demo contains synthetic Aadhaar and PAN cards. Their numbers are inside images. Local OCR finds those numbers, and our privacy pipeline masks them. Private portraits and sensitive fields are protected too. I can still read and use the original website.” |
| 0:55–1:30 | Open Support. Enter the custom draft prompt below, enable Draft only and run. Show the category and draft on the page. | “I can give a custom instruction. Here I ask the agent to select Technical and draft a reply without sending it. The model proposes actions, but local rules validate the target and the current page. Draft only blocks recognized sending actions before approval.” |
| 1:30–1:55 | Run a fresh synthetic consequential task and show its approval pause. Decline. | “Actions such as sending a reply or placing a demo order require my approval. Declining stops the action. Take control also returns the tab to me without closing my session.” |
| 1:55–2:20 | Show a privacy receipt and, optionally, Attack Lab. | “Receipts show the model destination, the amount of screened data and the fingerprint of the checked request. The leakage gate and local policy tests reject detected secrets or invalid secret use.” |
| 2:20–2:45 | Show Ollama selected and a completed local-model task. | “PrivacyLens can also use Ollama for on-device AI inference. Our contribution combines selective disclosure, scoped secret injection, approval and visible evidence in one browser workflow.” |

Custom support prompt: `Select Technical. Write “Please restart the demo app.” Do not send it.`

Use a short meeting mute task for the local-model segment if its latency fits the recording. If waiting periods are cut, label the edit “Waiting shortened.” Record actual outcomes rather than narrating success before it happens.

## Concepts to explain
- **Protected preview:** what local masking removes from a screenshot, not a replacement for the real website.
- **Secret reference:** the model requests an allowed field value by reference; local code checks scope and fills it.
- **Receipt:** a record of the checked model request, not a certificate of perfect privacy.
- **Attack Lab:** synthetic local misuse tests, not an attack on an external website.
- **Local AI:** the model runs through Ollama on this device. The deterministic test driver is a different testing tool.

Keep the explanation focused on the behavior visible in the recording. The five synthetic categories and SauceDemo are the supported extension scope.
