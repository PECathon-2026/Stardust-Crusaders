# Genuine browser extension

The `extension/` folder is a Manifest V3 browser extension. Its side panel sits beside the actual webpage. The user interacts directly with the website while the panel controls the agent.

## Start on this laptop

1. Keep the local PrivacyLens server running (`start.ps1`).
2. Run `launch-extension.ps1`. It opens a visible Chrome for Testing browser with the unpacked extension loaded. The dedicated profile is under `.runtime/extension-profile` on D:. It does not read your everyday browser profile or saved passwords.
3. The side panel opens automatically. Click **Open connection page**, copy the server session's code, paste it into the panel's **Connection code**, then click **Connect**.
4. Choose Ollama for a running local model, or in panel **Settings**, save a Gemini or Groq key. Keys stay in local-server memory. A server restart requires reconnecting and re-entering the provider key.
5. Open a demo from the panel, enter a prompt, select a planner and click **Run on this tab**.

For an existing compatible Chrome/Edge profile, use its extension management page, enable developer mode and load the project's `extension/` folder unpacked. Click the PrivacyLens toolbar icon to open the side panel. This installation route needs verification in the user's browser/version; the bundled Chrome for Testing route has been integration-tested.

The browser may display its normal debugger attachment banner during automation. This permission is used for same-tab DOM inspection, screenshots and input. It is not hidden or bypassed. Only the explicitly attached supported tab is controlled; passwords/cookies from the browser's password store are not queried.

## Manual control and credentials

- Log in manually on the website, optionally using your browser's ordinary autofill yourself. The extension does not read the password database.
- Or store specific values under panel **Settings → Local secret**. The model gets scoped references, not values.
- **Use synthetic demo secrets** is an explicit opt-in for the fake demo identities or SauceDemo's public demonstration account.
- **Take control** cancels the agent, invalidates pending approvals and detaches browser control. The actual tab and session stay open. Wait for the paused state before editing; an already-dispatched browser action cannot be recalled.
- **Run on this tab** after manual interaction starts a new run from a fresh observation. It does not replay the old action or reuse an old approval.
- **Stop & clear** also clears local secret overrides and run previews. It leaves your browser tab open.
- Changing active tabs or leaving the approved origin pauses control. Closing the side panel disconnects the local transport and stops the run.

## Privacy toggle (explicit choice, no Auto mode)

**Private workspace** is the default. Contextual names/faces are protected alongside credentials and identifiers. **Public browsing** permits names/faces in article/catalog/main-content regions, while recognized identifiers, known vault values, sensitive fields and marked private areas remain protected. This is a user-selected disclosure policy, not proof that a webpage is public or an infallible AI classifier. Do not choose Public for personal/account pages merely because they have a reachable URL.

Public/private section hints come from DOM semantics and are untrusted. Misleading page structure and unknown PII remain limitations. The stronger identifier/vault checks are not disabled by the toggle. The setting is fixed for a running task and appears in the observation and receipts.

## Architecture and boundaries

The extension pairs using a random server-session code. Ordinary website origins cannot pair. Only paired extension origins with the current session token can use the local API; the WebSocket also verifies origin and token. Pair attempts are rate-limited.

`chrome.debugger` transports a narrow browser adapter to the local service over a loopback WebSocket. The existing local detector/sanitizer, exact-byte model gateway, secret permissions, action validator and approval engine are reused. Browser commands are restricted to a supported attached tab; action handles and the observation fingerprint are checked before input. Raw DOM/screenshots travel to localhost for local processing, not directly to the cloud. The trusted local backend can issue browser evaluation commands; this is not a sandbox against a compromised local service.

Supported extension tabs: the five local demo categories and SauceDemo's login/inventory/cart. General arbitrary-site access is not implemented.

## Testing

See [hands-on acceptance tests](EXTENSION-TESTING.md) and [recorded evidence](EVALUATION.md).
