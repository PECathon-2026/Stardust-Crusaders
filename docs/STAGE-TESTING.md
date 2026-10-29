# Stage testing checkpoints

Current owner: Eshan (Silveroger), following the confirmed shared-device handoff.

## Stage: support context and Groq reliability

Implemented:
- Sanitized dropdown labels, choices and current selection in planner observations; option values stay local.
- Sanitized required-field/invalid-selection messages in task-bound context.
- Stop before a third identical proposal against the same semantic page state.
- Conservative rolling Groq token-budget estimation; waits are cancellable and shown in the dashboard. This cannot guarantee provider quota, especially if another application shares the account.
- Longer bounded task window for paced Groq runs; provider errors still stop without automatic retries.

Automated validation: 76 tests passed in the full run; a subsequently added repeated-click regression test also passed separately. Frontend production build passed. The restarted local test driver completed support, conference and developer tasks. Live validation of this stage is tracked separately and must not be inferred from these results.

## Try this stage yourself

1. Refresh the dashboard. In Settings, save the Groq API key (restart clears it).
2. Choose **Customer support**, **Groq**, and **Task-bound**. Start the default task. Expected: choose Billing, fill the public reply, request approval for Send reply, then verify Reply submitted after approval. The private conversation should remain masked.
3. Repeat with **Conference**. Expected: mute the microphone and verify completion; participant identities and chat remain masked.
4. Repeat with **Developer settings**. Expected: open key details, ask approval to revoke the synthetic key, then verify the demo key was revoked. Declining approval should stop the operation.
5. If a request-budget waiting message appears, wait for automatic continuation or press Stop to cancel. Do not repeatedly restart a task to bypass provider limits.
6. Compare the sanitized preview with the local original view and inspect receipts. Groq receipts should report text-only disclosure and a payload digest. The original view stays local.

Use synthetic credentials only. The **Local test driver** can exercise the same privacy/approval pipeline without a key, but it is deterministic and is not evidence of AI performance.

If a test fails, record the selected scenario and visible error. Do not include API keys or private original screenshots.

Next stage: complete live regression checks, then align the judging walkthrough and presentation with verified outcomes and known limitations.
