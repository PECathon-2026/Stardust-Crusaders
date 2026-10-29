"""Session pairing and same-tab runs for the browser side-panel extension."""
import asyncio
import re
import secrets
import time
from typing import Literal
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import Field
from .contracts import Strict, StartRequest, DEFAULT_TASKS
from .agent import Run
from .fixtures import values
from .extension_transport import ExtensionRPC, ExtensionBrowser

EXTENSION_ORIGIN = re.compile(r'^chrome-extension://[a-p]{32}$')
PAIR_CODE = secrets.token_hex(8)
PAIRED_ORIGINS = set()
PAIR_ATTEMPTS = {}
connection = None


class PairRequest(Strict):
    code: str = Field(min_length=1, max_length=64)


class TabRunRequest(Strict):
    url: str = Field(min_length=1, max_length=1500)
    task: str = Field(min_length=3, max_length=2000)
    provider: str = 'groq'
    demo_secrets: bool = False
    privacy_profile: Literal['private','public'] = 'private'


def tab_scenario(url):
    parsed = urlparse(url)
    if parsed.username or parsed.password or parsed.fragment:
        raise HTTPException(400, 'Unsupported tab URL')
    if parsed.scheme == 'http' and parsed.netloc == '127.0.0.1:8766':
        scenario = parsed.path.removeprefix('/scenario/')
        if scenario in ('checkout', 'authentication', 'support', 'conference', 'developer') and parsed.path == '/scenario/' + scenario:
            query = parse_qs(parsed.query)
            if set(query) <= {'seed', 'layout'}:
                return scenario
    if parsed.scheme == 'https' and parsed.netloc == 'www.saucedemo.com' and parsed.path in ('/', '/index.html', '/inventory.html', '/cart.html') and not parsed.query:
        return 'saucedemo'
    raise HTTPException(400, 'This tab is not enabled. Use a PrivacyLens demo page or SauceDemo. Wikipedia remains available only in the existing workspace.')


def install_extension(app, state):
    @app.get('/api/extension/pair-code')
    async def pair_code():
        return {'code': PAIR_CODE, 'connected': bool(connection and not connection.closed)}

    @app.post('/api/extension/pair')
    async def pair(payload: PairRequest, request: __import__('fastapi').Request):
        origin = request.headers.get('origin', '')
        if not EXTENSION_ORIGIN.fullmatch(origin):
            raise HTTPException(403, 'Pairing is only available to the browser extension')
        now = time.monotonic()
        attempts = [t for t in PAIR_ATTEMPTS.get(origin, []) if now-t < 60]
        if len(attempts) >= 5:
            raise HTTPException(429, 'Wait a minute before trying another connection code')
        attempts.append(now)
        PAIR_ATTEMPTS[origin] = attempts
        if not secrets.compare_digest(payload.code.strip(), PAIR_CODE):
            raise HTTPException(403, 'Connection code does not match this server session')
        PAIRED_ORIGINS.add(origin)
        return {'token': state.token}

    @app.websocket('/api/extension/ws')
    async def extension_socket(socket: WebSocket):
        global connection
        if socket.headers.get('host') not in ('127.0.0.1:8765', 'localhost:8765') or socket.headers.get('origin') not in PAIRED_ORIGINS:
            await socket.close(code=1008)
            return
        await socket.accept()
        rpc = None
        try:
            auth = await asyncio.wait_for(socket.receive_json(), 5)
            if not isinstance(auth, dict) or not isinstance(auth.get('token'), str) or not secrets.compare_digest(auth['token'], state.token):
                await socket.close(code=1008)
                return
            if connection and not connection.closed:
                await socket.close(code=1008)
                return
            rpc = ExtensionRPC(socket)
            connection = rpc
            await socket.send_json({'type':'ready'})
            while True:
                message = await socket.receive_json()
                if isinstance(message, dict) and message.get('type') == 'rpc_result':
                    rpc.receive(message)
        except (WebSocketDisconnect, asyncio.TimeoutError, ValueError):
            pass
        finally:
            if rpc:
                rpc.disconnect()
                if state.run and getattr(state.run.browser, 'rpc', None) is rpc:
                    if state.run.task and not state.run.task.done():
                        state.run.task.cancel()
                        try:
                            await state.run.task
                        except asyncio.CancelledError:
                            pass
                    state.run.status = 'paused'
                    state.run.approval = None
                    state.run.preview = None
                    state.run.event('Extension disconnected', 'Agent stopped; the website remains under your control', 'privacy')
                if connection is rpc:
                    connection = None

    @app.post('/api/extension/run')
    async def extension_run(payload: TabRunRequest):
        if state.initializing or not all(state.detector.status.get(k) for k in ('presidio','ocr')):
            raise HTTPException(409, 'Wait for local privacy detectors')
        if state.run and state.run.status in ('running','starting','awaiting_approval'):
            raise HTTPException(409, 'Pause or stop the current task first')
        if not connection or connection.closed:
            raise HTTPException(409, 'Connect the browser extension first')
        if payload.provider not in ('gemini','groq','ollama','demo'):
            raise HTTPException(400, 'Unsupported planner')
        if payload.provider == 'gemini' and not state.gateway.api_key or payload.provider == 'groq' and not state.gateway.groq_api_key:
            raise HTTPException(400, 'Save the selected provider key in the panel first')
        scenario = tab_scenario(payload.url)
        query = parse_qs(urlparse(payload.url).query)
        try:
            seed = int(query.get('seed', ['1'])[0])
            layout = int(query.get('layout', ['0'])[0])
            if not 1 <= seed <= 10000 or layout not in (0,1):
                raise ValueError()
        except ValueError:
            raise HTTPException(400, 'Invalid synthetic demo parameters') from None
        data = values(seed) if payload.demo_secrets else {}
        if payload.demo_secrets and scenario == 'saucedemo':
            data['password'] = data['sauce_password']
        data.update(state.settings_secrets)
        request = StartRequest(scenario=scenario, task=payload.task, provider=payload.provider, seed=seed, layout=layout, privacy_profile=payload.privacy_profile)
        adapter = ExtensionBrowser(state.detector, connection, payload.url)
        state.run = Run(request, adapter, state.gateway, data, payload.url)
        state.run.task = asyncio.create_task(state.run.loop(payload.url))
        return {'id':state.run.id}

    @app.post('/api/extension/pause')
    async def pause():
        run = state.run
        if run and getattr(run.browser, 'extension_mode', False):
            if run.task and not run.task.done():
                run.task.cancel()
                try:
                    await run.task
                except asyncio.CancelledError:
                    pass
            run.status = 'paused'
            run.approval = None
            run.preview = None
            await run.browser.close()
            run.event('You have control', 'No new agent actions. Resume starts from a fresh page observation.', 'privacy')
        return {'status':'paused'}

    @app.post('/api/extension/inspect')
    async def inspect(payload: TabRunRequest):
        tab_scenario(payload.url)
        if state.run and state.run.status in ('running','starting','awaiting_approval'):
            raise HTTPException(409, 'Take control before inspecting the page')
        if not connection or connection.closed:
            raise HTTPException(409, 'Connect the extension first')
        if state.initializing:
            raise HTTPException(409, 'Wait for local detectors')
        adapter = ExtensionBrowser(state.detector, connection, payload.url)
        await adapter.open(payload.url)
        preview = await adapter.capture(list(state.settings_secrets.values()), privacy_profile=payload.privacy_profile)
        return {'preview':preview, 'cloud_requests':0}

    @app.get('/extension-connect')
    async def connect_page():
        return FileResponse(state.ROOT / 'extension' / 'connect.html')

    @app.get('/extension-connect.js')
    async def connect_script():
        return FileResponse(state.ROOT / 'extension' / 'connect.js', media_type='text/javascript')
