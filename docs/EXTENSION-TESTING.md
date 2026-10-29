# Test the real PrivacyLens extension

Use the separate Chrome for Testing window. The actual website is on the left and PrivacyLens is on the right. The dashboard is optional evidence tooling, not the place to perform these steps. Keep the local server running. Your saved key remains available until the server restarts.

## First test: meeting (live Gemini verified)

1. In the panel's Task tab, expand **Open a demo website**, choose **Meeting**, and click **Open website in a new tab**. This opens a fresh synthetic meeting, with its example prompt filled in.
2. Select **Gemini**. Keep **Private workspace** selected. The prompt is: `Mute the microphone without exposing participant identities or private chat.`
3. Scroll down inside the panel and click **Run on this tab**. Leave this tab active while the task runs.
4. Expected: the real page displays **Microphone muted**, its button becomes **Unmute microphone**, and the panel verifies the outcome.
5. Open panel **Privacy**. The protected preview should hide participant photos/identities and private chat while keeping the microphone control visible. **Show local original** changes only the local preview; it does not send the original to the model. The real website remains readable to you.
6. Inspect the receipt: destination Gemini, protected categories, request size/hash and whether an image was disclosed. Ordinary text planning sends no screenshot. A hash identifies request bytes; it does not prove perfect privacy.

To repeat, open a fresh meeting using the demo menu. Running the mute task on an already-muted meeting may complete immediately without a new AI action.

## Other functional checks

For each row, open a fresh demo, use **Use this page's example**, and choose Gemini. These are supported flows to test; only the meeting is currently recorded as a successful live Gemini extension run.

| Demo | What you should see | Data demonstrated |
|---|---|---|
| Sign-in & identity | Enable **Use synthetic demo secrets**, then run. Fake fields fill locally and sign-in completes. Alternatively fill the fields yourself first. | Password, OTP, email, Aadhaar, PAN |
| Checkout | Enable synthetic demo secrets. Agent fills fake checkout fields and asks approval before placing the synthetic order. Deny first to verify it does not submit; approve on a fresh run to test completion. | Card, CVV, address |
| Support & health | Agent selects Billing, drafts the example reply, and asks approval before sending on the fake site. | Private messages and synthetic medical record |
| Developer console | Agent opens details and asks approval before revoking the fake key. | API key, token, IP, PAN |
| SauceDemo | Enable synthetic demo secrets for its public test account. Ask to log in, add the Sauce Labs Backpack, open the cart and stop before checkout. | External-site interaction; public product content |

For the SauceDemo catalog, try **Public browsing** while idle to preserve ordinary product content. Keep **Private workspace** for personal/account pages. Public mode still protects recognized strong identifiers, known secrets and explicitly private regions; it is not automatic public/private classification.

## Manual control

Start a task and click **Take control** before it finishes. Wait for paused state, then interact directly with the real page. It should remain open and editable. Run again to plan from its current state. **Stop & clear** clears run previews and local secret overrides without closing the tab. Switching tabs also pauses the agent.

## Current limits

- Only the five local demos and supported SauceDemo pages are enabled. This is not yet an arbitrary-site browser agent.
- Your password manager is not read. Log in yourself, use your browser's own autofill, or explicitly provide a local secret.
- Detectors can miss sensitive material or mask useful content. Report the page, prompt and wrong mask when that happens; do not submit real secrets in bug reports.
- The fixture purchase/reply/revocation and meeting controls are synthetic, not real transactions, messages, cloud-key changes or microphone access.
- Server restarts clear provider keys and pairing. Refresh the connection page, reconnect and save the key again when needed.
