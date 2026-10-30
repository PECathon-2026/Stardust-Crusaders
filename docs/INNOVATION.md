# Original contribution

PrivacyLens connects task-scoped disclosure with local action authority in a real browser extension. The user can see what the model receives and control what it may do.

## Distinctive mechanisms
1. **Task-minimal context:** share useful controls and selected status instead of the whole sanitized document.
2. **Progressive disclosure:** additional named image regions require approval and remain sanitized.
3. **Scoped secret use:** task, origin, field purpose and limited uses constrain local value resolution.
4. **Draft authority:** recognized consequential actions are blocked before approval when Draft only is active.
5. **Inspectable requests:** receipts connect model destinations, disclosed context and exact payload digests to local decisions.

The team built the extension workflow, contracts, enforcement, fixtures and evidence integration. Detection libraries and browser infrastructure are listed in [dependency credits](THIRD_PARTY.md).

## Comparison protocol
`benchmark.py` runs the same synthetic tasks with minimal context and full sanitized text. Keep detector, executor and approval policy fixed; compare observation bytes, turns and independently checked outcomes. The deterministic driver measures workflow and disclosure size. A model-quality comparison requires matched live-model runs in both modes.
