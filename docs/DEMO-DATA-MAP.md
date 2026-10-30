# Demo coverage by sensitive-data type

All local identities, credentials, financial details and records are synthetic. They are never real government identifiers or patient data collected from users.

| Requested category | Demo page | What to demonstrate |
|---|---|---|
| Aadhaar | Sign-in / identity | Synthetic identity number remains masked while sign-in controls stay usable |
| PAN | Sign-in / identity and developer billing | PAN is protected independently of ordinary public text |
| Password | Sign-in, or SauceDemo public test account | User types locally or permits local secret injection; model sees only field state/reference |
| OTP | Sign-in | Local one-time-code fill; value stays out of model context |
| Financial details | Checkout | Card/address/CVV protection, local fill, approval before synthetic order |
| API keys/tokens | Developer workspace | Key masked; approval before synthetic revocation |
| Medical records | Support / health | Explicit synthetic patient/lab/follow-up record in a private region |
| Personal messages | Support and meeting | Private conversation/chat protected while useful controls remain |
| Faces and participant identity | Meeting | Private participant regions and detected faces protected |
| Public information | SauceDemo catalog, public-browsing toggle | Product photos, labels and controls remain useful; demonstrate the difference from private account data |

The exact demo actions remain independently verified fixture outcomes: sign-in, purchase, reply submitted, microphone muted and demo key revoked. The extension operates on the real open fixture tab. These controlled sites demonstrate privacy with reproducible inputs; SauceDemo is the external public test-site example.
