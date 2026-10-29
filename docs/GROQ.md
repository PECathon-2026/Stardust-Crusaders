# Groq text planner

Refresh the dashboard, open Settings (gear), paste the Groq key into **Groq API key**, and select **Save session settings**. Saving a new Groq key selects the Groq planner. The key remains in backend memory and clears on restart. No .env file is needed. Never commit keys.

Default model: `openai/gpt-oss-120b`. The adapter sends the exact sanitized and hashed JSON bytes to Groq's chat completions endpoint. Provider credentials are separate from Gemini's. Strict structured output constrains proposals; local action validation, secret capabilities and approval checks still authorize execution.

This is text-only planning. Screenshot detection and masking remain local. Image disclosure is omitted from the Groq action schema and rejected before transport. Free accounts have quota limits; a 429 stops the run safely without automatic retries. Saved configuration is not proof of provider access or task success.

Live validation initially reached Groq but received HTTP 400 classified as a schema rejection. The original nested action union has been replaced for Groq by one fixed object with required nullable fields. The local validator retains the per-action field rules, 500-character text limit, current snapshot and target restrictions. No raw-data fallback is permitted. The provider error supplied by the user identified `discriminator_multiple_candidates`: both snapshot_id and type were treated as candidates in the action union. Live testing confirmed the fixed shape is accepted (HTTP 200).

Validation: 11 mocked Groq test cases cover transport bytes, key separation, missing keys, rejected image input, safe diagnostics, nullable fields, and enforcement against stale/invented/misapplied targets, extra action fields and oversized text. Together with existing policy/control/failure tests, 59 tests pass. Dashboard build passes and the password field is checked on the restarted server. Live results are saved in `live-groq-results.json`: checkout completed with verified purchase (7 steps, 30.75s), authentication completed with verified signin (5 steps, 21.53s). Support repeated fill/click actions and was blocked by HTTP 429 on step 10; conference and developer were not attempted after the quota error. This is 2/3 attempted tasks completed, not a five-task success claim. The support planning loop and free-tier request pacing remain open. The full automated suite subsequently passed: 73 tests, one dependency deprecation warning.

References: [structured outputs](https://console.groq.com/docs/structured-outputs), [rate limits](https://console.groq.com/docs/rate-limits), [key console](https://console.groq.com/keys).

## Reliability follow-up (Eshan)
The next stage adds sanitized dropdown choices/current selection and validation feedback, a repeated-action guard and a rolling request budget estimated from payload bytes plus output allowance. Waiting is cancellable and shown in the dashboard. Shared-account activity and estimator error can still produce 429 responses; no automatic error retries are made. Live validation of this stage is pending; see STAGE-TESTING.md.
