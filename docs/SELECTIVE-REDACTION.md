# Selective redaction correction

The earlier visual policy obscured all image/media elements and all text fields. A sensitive match also masked the entire DOM text node. This hid public product images and useful text; completing tasks did not establish good context preservation.

The correction:
- Ordinary `img` elements are scanned with OCR and face detection rather than blanket-masked. Private-region images remain fully masked. Canvas/video/iframe/unsupported media remain conservative. If face detection is unavailable, image masking falls back to the conservative policy.
- DOM text uses per-finding character ranges, preserving surrounding public words. Unicode offsets are converted to DOM UTF-16 offsets. Missing geometry falls back to masking the full text node, and changed page state fails closed.
- Harmless search/reply fields are no longer automatically obscured. Recognized sensitive-purpose fields, passwords and fields containing detected or known private values remain masked. Field values still stay out of the model observation.
- Narrow, origin-scoped public brand/product dictionaries suppress only mistaken Presidio PERSON matches. They apply consistently to DOM text and OCR. Pattern-detected secrets and known vault values are never exempt.
- OCR also receives known private values, strengthening detection of those values inside image text.

Real-page checks found zero blanket masks over public images on Wikipedia and SauceDemo. Screenshots were visually inspected: product photos and branding remain visible. Some public description/article text still receives false-positive NER/OCR masks; these remain a known limitation. Face masking also applies to public images and is not a public-figure classifier.

Tests cover private-media masking, conservative fallback without faces, sensitive-span geometry, search-field preservation and private-value protection. The full suite passed 88 cases before the final search-field test; the expanded 18-test browser suite then passed. The independent 50-screenshot annotated privacy evaluation is rerun for this revision; see pixel-results.json for current measurements. This corpus does not establish arbitrary-webpage accuracy.

Demo selection: Wikipedia establishes recognizable-site navigation. SauceDemo demonstrates public catalog preservation plus local demonstration credentials. The synthetic checkout, support and developer pages explicitly expose the privacy boundary, approval decisions and blocked leaks using reproducible fake data. Do not imply that an ordinary public Wikipedia page contains the same privacy risks as a private account page.


Selective-redaction validation: 130/130 annotated text regions covered in 50 screenshots; median 2286 ms, p95 3351 ms (still above the 3-second target). Real-site checks preserved public images, but public-text false positives remain. The full suite passed 88 tests before the final search-field test; the expanded browser suite passed all 18 tests afterward.
