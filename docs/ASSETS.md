# Synthetic visual fixture

`assets/fictional-participant.png` was generated with Codex's built-in image generation tool, inspected, and copied into this project. It depicts a fictional adult, not an actual conference participant. Both conference tiles intentionally reuse the same fixture to test multiple visible regions. No identity recognition is performed.

Generation prompt: “Use case: photorealistic-natural. Asset type: synthetic face-detection test fixture for a privacy-preserving browser hackathon project. Create one square photograph of one entirely fictional adult person, not a celebrity or real person, front-facing head and shoulders in a simple home-office video-call setting. Clearly visible natural human face, neutral expression, even daylight, no glasses, no text, no watermarks. Face centered and occupying about 40 percent of image width. This is a synthetic test asset, not a real person's identity.”

Face detector scores on this one image do not establish general face-detection accuracy. Conservative image masking independently covers the entire conference image, even if YuNet misses a face.


## Synthetic identity scans
`assets/synthetic-aadhaar.png` and `assets/synthetic-pan.png` are reproducible, locally drawn PNG test cards from `generate_identity_assets.py`. They are prominently marked SYNTHETIC SAMPLE / NOT VALID ID and contain no real identity, official logos, signatures or QR codes. The numbers are image pixels, not webpage text or alt values. This is a clean-scan OCR demonstration, not a realistic government-document reproduction. Independent number-region annotations are in docs/identity-image-annotations.json and are used only by evaluation.
