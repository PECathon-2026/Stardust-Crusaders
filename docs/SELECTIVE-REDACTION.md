# Selective redaction

PrivacyLens preserves useful public content while screening sensitive spans and image regions locally.

- DOM findings map to character ranges rather than entire text nodes. Missing geometry uses conservative coverage.
- Ordinary images use OCR and face detection. Explicitly private media receive complete masks. Unsupported media surfaces use conservative handling.
- Sensitive-purpose fields and fields containing detected or known private values are protected. Field values do not enter the planner observation.
- Narrow origin-scoped product/brand dictionaries suppress mistaken PERSON matches without exempting recognized secrets.
- Private workspace protects contextual names and faces. Public browsing preserves names/faces in public-content regions while retaining identifier, secret and private-region protection.
- A changed page invalidates the observation and triggers bounded recapture or a safe stop.

The profile is a user choice. DOM hints and detector confidence do not establish whether every piece of data is public. Test public catalog preservation in SauceDemo and sensitive data in the synthetic fixtures. See [tests](EXTENSION-TESTING.md) and [evaluation](EVALUATION.md).
