"""Local text/image processing. No outbound requests are permitted from detection methods."""

import base64, hashlib, io, re, time, unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from PIL import Image, ImageDraw


class PrivacyError(Exception):
    pass


class StaleObservation(PrivacyError):
    pass


@dataclass
class Finding:
    kind: str
    start: int
    end: int
    source: str
    reason: str


# Three patterns adapted from Gitleaks. See docs/THIRD_PARTY.md for provenance.
RULES = [
    ("API_KEY", r"ghp_[0-9a-zA-Z]{36}", "gitleaks/github-pat"),
    (
        "API_KEY",
        r"\b(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z2-7]{16}\b",
        "gitleaks/aws-access-token",
    ),
    ("API_KEY", r"\bAIza[\w-]{35}", "gitleaks/gcp-api-key"),
    (
        "API_KEY",
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b",
        "local/token",
    ),
    (
        "API_KEY",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "local/private-key",
    ),
    (
        "EMAIL_ADDRESS",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "local/email",
    ),
    ("IN_PAN", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "local/pan"),
    ("PHONE_NUMBER", r"(?<!\w)(?:\+91[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)", "local/phone"),
    ("IP_ADDRESS", r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])", "local/ip"),
    ("CREDIT_CARD", r"(?<!\w)(?:\d[ -]?){13,19}(?!\w)", "local/card-candidate"),
    (
        "IN_AADHAAR",
        r"(?<!\w)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\w)",
        "local/aadhaar-candidate",
    ),
    (
        "ADDRESS",
        r"\b\d{1,5}\s+[A-Za-z ]{2,45}(?:Lane|Road|Street|Avenue|Rd|St)\b[^\n<]{0,45}",
        "local/address-context",
    ),
]


def luhn(text):
    digits = [int(c) for c in text if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    return (
        sum(
            (d * 2 - 9 if d * 2 > 9 else d * 2) if i % 2 else d
            for i, d in enumerate(reversed(digits))
        )
        % 10
        == 0
    )


def normalized(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFKC", text)
        if unicodedata.category(c) != "Cf"
    )


class Detector:
    def __init__(self):
        self.analyzer = None
        self.ocr = None
        self.face = None
        self.status = {
            "patterns": True,
            "presidio": False,
            "ocr": False,
            "faces": False,
        }

    def initialize(self):
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            engine = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
                }
            ).create_engine()
            self.analyzer = AnalyzerEngine(
                nlp_engine=engine, supported_languages=["en"]
            )
            self.status["presidio"] = True
        except Exception:
            self.status["presidio"] = False
        try:
            from rapidocr import RapidOCR

            self.ocr = RapidOCR(
                params={
                    "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                    "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                    "Global.log_level": "warning",
                }
            )
            self.status["ocr"] = True
        except Exception:
            self.status["ocr"] = False
        try:
            import cv2

            model = Path(__file__).resolve().parents[1] / "models" / "yunet.onnx"
            if model.exists() and model.stat().st_size > 10000:
                self.face = cv2.FaceDetectorYN.create(
                    str(model), "", (320, 320), 0.7, 0.3, 5000
                )
                self.status["faces"] = True
        except Exception:
            self.status["faces"] = False
        return self.status

    def detect(self, text, context="", include_nlp=True):
        if not isinstance(text, str):
            raise PrivacyError("Invalid detector input")
        findings = []
        # Map normalized character positions to original string positions.
        chars = []
        positions = []
        for i, c in enumerate(text):
            for n in normalized(c):
                chars.append(n)
                positions.append(i)
        clean = "".join(chars)
        for kind, pattern, source in RULES:
            for m in re.finditer(pattern, clean):
                if kind == "CREDIT_CARD" and not luhn(m.group()):
                    continue
                if kind == "IP_ADDRESS" and any(
                    int(p) > 255 for p in m.group().split(".")
                ):
                    continue
                findings.append(
                    Finding(
                        kind,
                        positions[m.start()],
                        positions[m.end() - 1] + 1,
                        source,
                        "Local pattern/context",
                    )
                )
        for m in re.finditer(
            r'(?i)(?:api[_ -]?key|bearer|token|password)\s*[:= ]\s*["\']?([A-Za-z0-9_!@#$%^&*+/.=-]{6,})',
            clean,
        ):
            findings.append(
                Finding(
                    "SECRET",
                    positions[m.start(1)],
                    positions[m.end(1) - 1] + 1,
                    "local/secret-context",
                    "Secret assignment",
                )
            )
        if include_nlp and self.analyzer and text.strip():
            results = self.analyzer.analyze(
                text=text,
                language="en",
                score_threshold=0.65,
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "IP_ADDRESS",
                    "IN_PAN",
                    "IN_AADHAAR",
                ],
            )
            for r in results:
                if r.entity_type == "PERSON" and len(text[r.start : r.end].split()) < 2:
                    continue
                findings.append(
                    Finding(
                        r.entity_type, r.start, r.end, "presidio", "Local recognizer"
                    )
                )
        # Merge overlapping evidence conservatively. No entity values in public findings.
        merged = []
        for f in sorted(findings, key=lambda f: (f.start, -f.end)):
            if merged and f.start < merged[-1].end:
                merged[-1].end = max(merged[-1].end, f.end)
            else:
                merged.append(f)
        return merged

    def sanitize(self, text, known=(), public_literals=(), public_context=False):
        findings = self.detect(text)
        if public_context:
            # Explicit public-content policy suppresses name classification only.
            # Strong identifiers and known local secrets still take precedence.
            findings = [f for f in findings if f.kind != 'PERSON']
        public_spans = [
            (m.start(), m.end())
            for value in public_literals
            for m in re.finditer(re.escape(value), text)
        ]
        findings = [
            f
            for f in findings
            if not (
                f.kind == "PERSON"
                and f.source == "presidio"
                and any(a <= f.start and f.end <= b for a, b in public_spans)
            )
        ]
        for secret in known:
            if len(secret) >= 3:
                for m in re.finditer(re.escape(secret), text):
                    findings.append(
                        Finding(
                            "SECRET",
                            m.start(),
                            m.end(),
                            "local/vault",
                            "Known private value",
                        )
                    )
        merged = []
        for f in sorted(findings, key=lambda f: (f.start, -f.end)):
            if merged and f.start < merged[-1].end:
                merged[-1].end = max(merged[-1].end, f.end)
            else:
                merged.append(f)
        for f in reversed(merged):
            text = text[: f.start] + f"[REDACTED:{f.kind}]" + text[f.end :]
        return text, merged

    def visual_boxes(self, png, known=(), public_literals=(), public_regions=()):
        import numpy as np

        image = Image.open(io.BytesIO(png)).convert("RGB")
        arr = np.asarray(image)
        boxes = []
        def public_box(x, y, width, height):
            return any(x >= r['x'] and y >= r['y'] and x+width <= r['x']+r['width'] and y+height <= r['y']+r['height'] for r in public_regions)
        if self.ocr:
            result = self.ocr(arr)
            if result.txts is not None:
                for box, text in zip(result.boxes, result.txts):
                    xs = [float(p[0]) for p in box]
                    ys = [float(p[1]) for p in box]
                    _, findings = self.sanitize(str(text), known, public_literals, public_context=public_box(min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)))
                    if findings:
                        xs = [float(p[0]) for p in box]
                        ys = [float(p[1]) for p in box]
                        boxes.append(
                            {
                                "x": min(xs),
                                "y": min(ys),
                                "width": max(xs) - min(xs),
                                "height": max(ys) - min(ys),
                                "kind": findings[0].kind,
                                "source": "ocr",
                            }
                        )
        if self.face:
            import cv2

            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            self.face.setInputSize((image.width, image.height))
            _, faces = self.face.detect(bgr)
            if faces is not None:
                for f in faces:
                    if public_box(float(f[0]),float(f[1]),float(f[2]),float(f[3])):
                        continue
                    boxes.append(
                        {
                            "x": float(f[0]),
                            "y": float(f[1]),
                            "width": float(f[2]),
                            "height": float(f[3]),
                            "kind": "FACE",
                            "source": "yunet",
                        }
                    )
        return boxes


def redact_image(png, boxes):
    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image)
    for b in boxes:
        x = max(0, int(b["x"]) - 3)
        y = max(0, int(b["y"]) - 3)
        x2 = min(image.width, int(b["x"] + b["width"]) + 4)
        y2 = min(image.height, int(b["y"] + b["height"]) + 4)
        if x2 <= x or y2 <= y:
            continue
        draw.rectangle((x, y, x2, y2), fill="#183e37")
        if y2 - y > 19 and x2 - x > 65:
            draw.text((x + 5, y + 4), "PROTECTED", fill="#b8eac7")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def image_url(data):
    return "data:image/png;base64," + base64.b64encode(data).decode()


def leak_check(payload, known, detector, approved_image=None):
    import json, urllib.parse

    raw = payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
    # Only exact compositor output may bypass text inspection, at the provider image path.
    obj = json.loads(raw)

    def walk(v, path=()):
        if isinstance(v, str):
            if approved_image is not None and path == (
                "contents",
                0,
                "parts",
                1,
                "inline_data",
                "data",
            ):
                if v != base64.b64encode(approved_image).decode():
                    raise PrivacyError("Unapproved image payload")
                return
            if v.startswith("data:image/png;base64,"):
                raise PrivacyError("Unexpected image field")
            decoded = urllib.parse.unquote(normalized(v))
            for secret in known:
                if len(secret) < 3:
                    continue
                for candidate in (
                    normalized(secret),
                    base64.b64encode(secret.encode()).decode(),
                ):
                    # Short numeric secrets must match a token, not random opaque identifiers.
                    matched = (
                        re.search(
                            r"(?<![A-Za-z0-9])"
                            + re.escape(candidate)
                            + r"(?![A-Za-z0-9])",
                            decoded,
                        )
                        if len(secret) < 6
                        else candidate in decoded
                    )
                    if matched:
                        raise PrivacyError("Known private value in outgoing payload")
            safe = re.sub(r"\[REDACTED:[A-Z_]+\]", "", v)
            findings = detector.detect(safe, include_nlp=False)
            if findings:
                raise PrivacyError(
                    "Unredacted sensitive text in outgoing payload ("
                    + findings[0].kind
                    + ")"
                )
        elif isinstance(v, list):
            for i, item in enumerate(v):
                walk(item, path + (i,))
        elif isinstance(v, dict):
            for k, value in v.items():
                walk(k, path + ("key",))
                walk(value, path + (k,))

    walk(obj)
    return hashlib.sha256(raw.encode()).hexdigest()
