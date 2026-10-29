import asyncio, json, os, secrets
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from .contracts import (
    StartRequest,
    SettingsRequest,
    ApprovalRequest,
    DEFAULT_TASKS,
    SecretEntry,
    PromptRequest,
)
from .privacy import Detector
from .browser import Browser
from .agent import Gateway, Run
from .fixtures import fixture, values
from .evaluation import attack_lab, evaluate_text

ROOT = Path(__file__).resolve().parents[1]
token = secrets.token_urlsafe(32)
detector = Detector()
gateway = Gateway(detector)
browser = Browser(detector)
run = None
initializing = True
headless = True
settings_secrets = {}
evaluation = None
gateway.api_key = os.getenv("GEMINI_API_KEY", "")
gateway.groq_api_key = os.getenv("GROQ_API_KEY", "")
gateway.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


@asynccontextmanager
async def lifespan(app):
    global initializing

    async def initialize():
        global initializing
        await asyncio.to_thread(detector.initialize)
        initializing = False

    init = asyncio.create_task(initialize())
    yield
    init.cancel()
    if run and run.task:
        run.task.cancel()
    await browser.close()


app = FastAPI(
    title="PrivacyLens local control", lifespan=lifespan, docs_url=None, redoc_url=None
)
fixtures = FastAPI(docs_url=None, redoc_url=None)
fixtures.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="fixture-assets")


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Framework validation details may echo submitted secret values.
    return JSONResponse({"detail": "Request fields are invalid"}, status_code=422)


@app.middleware("http")
async def boundary(request: Request, call_next):
    origin = request.headers.get("origin")
    host = request.headers.get("host", "")
    allowed = {"127.0.0.1:8765", "localhost:8765", "testserver"}
    from .extension_api import EXTENSION_ORIGIN, PAIRED_ORIGINS
    extension_origin = bool(origin and EXTENSION_ORIGIN.fullmatch(origin))
    pairing = request.url.path == '/api/extension/pair' and extension_origin
    if host not in allowed:
        return JSONResponse({"detail": "Host rejected"}, status_code=403)
    if origin and origin not in {"http://127.0.0.1:8765", "http://localhost:8765"} and origin not in PAIRED_ORIGINS and not pairing:
        return JSONResponse({"detail": "Origin rejected"}, status_code=403)
    if request.headers.get("sec-fetch-site") == "cross-site" and origin not in PAIRED_ORIGINS and not pairing:
        return JSONResponse(
            {"detail": "Cross-site control request rejected"}, status_code=403
        )
    if request.method == 'OPTIONS' and extension_origin and (pairing or origin in PAIRED_ORIGINS):
        return JSONResponse({}, headers={'Access-Control-Allow-Origin':origin, 'Access-Control-Allow-Methods':'GET, POST, OPTIONS', 'Access-Control-Allow-Headers':'content-type,x-privacy-session'})
    if request.url.path.startswith("/api/") and request.url.path != "/api/bootstrap" and not pairing:
        if not secrets.compare_digest(
            request.headers.get("x-privacy-session", ""), token
        ):
            return JSONResponse({"detail": "Session required"}, status_code=401)
    response = await call_next(request)
    if extension_origin and (pairing or origin in PAIRED_ORIGINS):
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
    return response


@app.get("/api/bootstrap")
async def bootstrap():
    return {"token": token}


@app.get("/api/status")
async def status():
    return {
        "initializing": initializing,
        "detectors": detector.status,
        "groq_configured": bool(gateway.groq_api_key),
        "groq_model": gateway.groq_model,
        "gemini_configured": bool(gateway.api_key),
        "gemini_model": gateway.model,
        "provider_status": gateway.provider_status,
        "headless": headless,
        "scenarios": DEFAULT_TASKS,
        "run": run.public() if run else None,
        "evaluation": evaluation,
    }


@app.post("/api/settings")
async def settings(payload: SettingsRequest):
    global headless
    if run and run.status in ("running", "starting", "awaiting_approval"):
        raise HTTPException(409, "Stop the run before changing settings")
    if payload.api_key:
        gateway.api_key = payload.api_key
    if payload.api_key or gateway.model != payload.gemini_model:
        gateway.provider_status = None
    if payload.groq_api_key or gateway.groq_model != payload.groq_model:
        gateway.provider_status = None
    if payload.groq_api_key:
        gateway.groq_api_key = payload.groq_api_key
    gateway.groq_model = payload.groq_model
    gateway.model = payload.gemini_model
    headless = payload.headless
    return {"configured": bool(gateway.api_key), "model": gateway.model}


@app.post("/api/secrets")
async def set_secret(payload: SecretEntry):
    if run and run.status in ("running", "starting", "awaiting_approval"):
        raise HTTPException(409, "Stop the run before changing secrets")
    settings_secrets[payload.reference] = payload.value
    return {"reference": payload.reference, "stored": "memory only"}


@app.post("/api/runs")
async def start(payload: StartRequest):
    global run
    if initializing:
        raise HTTPException(409, "Local detectors are initializing")
    if run and run.status in ("running", "starting", "awaiting_approval"):
        raise HTTPException(409, "A task is already running")
    if not all(detector.status[k] for k in ["presidio", "ocr"]):
        raise HTTPException(
            503, "Required local detectors are unavailable. Run setup.ps1."
        )
    if payload.provider == "gemini" and not gateway.api_key:
        raise HTTPException(400, "Add your Gemini key in Settings first")
    if payload.provider == "groq" and not gateway.groq_api_key:
        raise HTTPException(400, "Add your Groq key in Settings first")
    payload.task = payload.task or DEFAULT_TASKS[payload.scenario]
    url = {
        "wikipedia": "https://en.wikipedia.org/wiki/Main_Page",
        "saucedemo": "https://www.saucedemo.com/",
    }.get(
        payload.scenario,
        f"http://127.0.0.1:8766/scenario/{payload.scenario}?seed={payload.seed}&layout={payload.layout}",
    )
    data = values(payload.seed)
    if payload.scenario == "saucedemo":
        data["password"] = data["sauce_password"]
    data.update(settings_secrets)
    run = Run(payload, browser, gateway, data, url)
    run.task = asyncio.create_task(run.loop(url, headless))
    return {"id": run.id}


SUPPORTED_PAGES = {
    **{f"http://127.0.0.1:8766/scenario/{s}": s for s in ("checkout", "authentication", "support", "conference", "developer")},
    "https://en.wikipedia.org/wiki/Main_Page": "wikipedia",
    "https://www.saucedemo.com/": "saucedemo",
}


@app.get("/api/pages")
async def supported_pages():
    return {"pages": [{"url": url, "name": name, "example": DEFAULT_TASKS[name]} for url, name in SUPPORTED_PAGES.items()]}


@app.post("/api/agent/runs")
async def prompt_run(payload: PromptRequest):
    # Exact allowlist: no user-controlled URLs enter the browser or network.
    scenario = SUPPORTED_PAGES.get(payload.url.strip())
    if not scenario:
        raise HTTPException(400, "This page is not supported yet. Choose a listed page; arbitrary sites are not enabled.")
    return await start(StartRequest(scenario=scenario, task=payload.task, provider=payload.provider))


@app.post("/api/stop")
async def stop():
    global run
    if run:
        run.stop = True
        if run.task:
            run.task.cancel()
            try:
                await run.task
            except asyncio.CancelledError:
                pass
        run.vault.values.clear()
        run.known.clear()
        run.preview = None
        run.status = "stopped"
        if run.browser is not browser:
            await run.browser.close()
    await browser.close()
    settings_secrets.clear()
    return {"status": "stopped", "local_values_cleared": True}


@app.post("/api/approve")
async def approve(payload: ApprovalRequest):
    if (
        not run
        or not run.approval
        or not secrets.compare_digest(run.approval["id"], payload.approval_id)
    ):
        raise HTTPException(409, "Approval is missing or stale")
    run.pending = payload.approved
    run.decision.set()
    return {"accepted": True}


@app.post("/api/attack-lab")
async def attacks():
    return await asyncio.to_thread(attack_lab, detector)


@app.post("/api/evaluate")
async def evaluate():
    global evaluation
    if initializing:
        raise HTTPException(409, "Wait for detectors")
    if run and run.status in ("running", "starting", "awaiting_approval"):
        raise HTTPException(409, "Stop the task before evaluating")
    evaluation = await asyncio.to_thread(evaluate_text, detector)
    (ROOT / ".runtime").mkdir(exist_ok=True)
    (ROOT / ".runtime" / "evaluation.json").write_text(
        json.dumps(evaluation, indent=2), encoding="utf-8"
    )
    return evaluation


@app.get("/api/export")
async def export():
    return {
        "project": "PrivacyLens",
        "evaluation": evaluation,
        "receipts": run.receipts if run else [],
        "scope": "Application-controlled pathways; no universal privacy guarantee.",
    }


@fixtures.get("/scenario/{scenario}", response_class=HTMLResponse)
async def scenario(scenario: str, seed: int = 1, layout: int = 0):
    if scenario not in [
        "checkout",
        "authentication",
        "support",
        "conference",
        "developer",
    ]:
        raise HTTPException(404)
    return fixture(scenario, max(1, min(seed, 10000)), layout % 2)[0]


@fixtures.post("/verify")
async def verify_fixture(request: Request, seed: int = 1):
    body = await request.json()
    fields = body.get("fields", {})
    v = values(max(1, min(seed, 10000)))
    scenario = body.get("scenario")
    action = body.get("action")
    required = {
        "checkout": ("purchase", ["name", "address", "card", "cvv"]),
        "authentication": ("signin", ["email", "password", "otp"]),
    }
    valid = False
    if scenario in required:
        expected, keys = required[scenario]
        valid = action == expected and all(fields.get(k) == v[k] for k in keys)
    elif scenario == "support":
        valid = (
            action == "send"
            and fields.get("category") == "Billing"
            and fields.get("reply") == "I can help with your billing question."
        )
    elif scenario == "conference":
        valid = action == "mute"
    elif scenario == "developer":
        valid = action == "revoke"
    return JSONResponse({"verified": valid}, status_code=200 if valid else 422)


dist = ROOT / "frontend" / "dist"
from .extension_api import install_extension
import sys
install_extension(app, sys.modules[__name__])
if (dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")


@app.get("/")
@app.get("/lab")
async def home():
    if (dist / "index.html").exists():
        return FileResponse(dist / "index.html")
    return HTMLResponse(
        "<h1>PrivacyLens</h1><p>Frontend not built. Run setup.ps1, then start.ps1.</p>"
    )
