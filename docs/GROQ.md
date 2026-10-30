# Groq text planner

In extension Settings, enter a Groq API key and save provider settings. Select Groq in the Task view. Keys stay in local-server memory and clear on restart; no `.env` is required.

The adapter uses `openai/gpt-oss-120b` and a fixed structured action object. Snapshot, target and per-action restrictions are enforced locally. The exact sanitized and hashed JSON body is transmitted to the provider.

Groq receives text only. Image disclosure is rejected before transport; screenshot screening and previews remain local. Request pacing uses a rolling token-budget estimate with cancellable waits. Shared-account use can still cause quota errors. Provider failures stop the run without raw fallback or automatic retry.

See [evaluation](EVALUATION.md) for recorded task evidence and [hands-on tests](EXTENSION-TESTING.md) for current workflows.

Provider references: [keys](https://console.groq.com/keys), [structured outputs](https://console.groq.com/docs/structured-outputs), [rate limits](https://console.groq.com/docs/rate-limits).
