"""A narrow browser adapter over an explicitly paired extension connection.

Raw page data stays between the browser and localhost. Gateway is still the only
model transport. The adapter never launches, navigates, or closes the user's tab.
"""
import asyncio
import base64
import io
import json
import secrets
from PIL import Image
from .browser import Browser, FINGERPRINT
from .privacy import PrivacyError, StaleObservation


class ExtensionRPC:
    def __init__(self, socket):
        self.socket = socket
        self.pending = {}
        self.closed = False

    async def call(self, method, **params):
        if self.closed:
            raise PrivacyError("Browser extension disconnected")
        request_id = secrets.token_hex(12)
        future = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        try:
            await self.socket.send_json({"type": "rpc", "id": request_id, "method": method, "params": params})
            return await asyncio.wait_for(future, 25)
        except asyncio.TimeoutError:
            raise PrivacyError("Browser extension did not respond. Take control and reconnect.") from None
        finally:
            self.pending.pop(request_id, None)

    def receive(self, message):
        future = self.pending.get(message.get('id'))
        if future is None or future.done():
            return
        if message.get('ok') is True:
            future.set_result(message.get('result'))
        else:
            future.set_exception(PrivacyError("Browser command stopped: tab changed, user took control, or target is unavailable."))

    def disconnect(self):
        self.closed = True
        for future in list(self.pending.values()):
            if not future.done():
                future.set_exception(PrivacyError("Browser extension disconnected"))


class ExtensionLocator:
    def __init__(self, page, selector):
        self.page, self.selector = page, selector

    @property
    def first(self):
        return self

    async def _read(self, expression):
        return await self.page.evaluate(f"() => {{ const elements=Array.from(document.querySelectorAll({json.dumps(self.selector)})); return ({expression}); }}")

    async def count(self):
        return await self._read('elements.length')

    async def is_visible(self):
        return await self._read("elements.length===1 && elements[0].getBoundingClientRect().width>0 && elements[0].getBoundingClientRect().height>0 && getComputedStyle(elements[0]).visibility!=='hidden'")

    async def is_enabled(self):
        return await self._read('elements.length===1 && !elements[0].disabled')

    async def inner_text(self):
        return await self._read("elements[0]?.innerText || ''")

    async def all_text_contents(self):
        return await self._read("elements.map(e=>e.textContent)")

    async def click(self, **kwargs):
        await self.page.rpc.call('action', action='click', selector=self.selector)

    async def fill(self, value, **kwargs):
        await self.page.rpc.call('action', action='fill', selector=self.selector, value=value)

    async def select_option(self, label, **kwargs):
        await self.page.rpc.call('action', action='select', selector=self.selector, value=label)


class ExtensionMouse:
    def __init__(self, page):
        self.page = page

    async def wheel(self, x, y):
        await self.page.rpc.call('action', action='scroll', delta=y)


class ExtensionPage:
    def __init__(self, rpc, url):
        self.rpc, self.url = rpc, url
        self.mouse = ExtensionMouse(self)

    async def evaluate(self, source, arg=None):
        expression = f"({source})({json.dumps(arg, ensure_ascii=True)})" if '=>' in source or source.lstrip().startswith('function') else source
        result = await self.rpc.call('evaluate', expression=expression)
        self.url = result['url']
        return result['value']

    async def screenshot(self, **kwargs):
        result = await self.rpc.call('screenshot')
        self.url = result['url']
        raw = base64.b64decode(result['data'], validate=True)
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        size = (int(result['width']), int(result['height']))
        if not (0 < size[0] <= 6000 and 0 < size[1] <= 6000):
            raise PrivacyError('Unsupported browser viewport')
        if image.size != size:
            image = image.resize(size)
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()

    def locator(self, selector):
        return ExtensionLocator(self, selector)

    async def wait_for_timeout(self, milliseconds):
        await asyncio.sleep(milliseconds / 1000)


class ExtensionBrowser(Browser):
    def __init__(self, detector, rpc, url):
        super().__init__(detector)
        self.rpc = rpc
        self.initial_url = url
        self.extension_mode = True

    async def open(self, url, headless=True):
        self.page = ExtensionPage(self.rpc, url)
        actual = await self.page.evaluate('location.href')
        if self.get_origin(actual) != self.get_origin(url):
            raise PrivacyError('Selected tab origin changed before starting')
        self.origin = self.get_origin(actual)

    async def execute(self, action, secret=None):
        # The extension also checks this fingerprint immediately before dispatch.
        await self.rpc.call('guard', fingerprint=self.fingerprint, expression=f'({FINGERPRINT})()')
        await super().execute(action, secret)

    async def close(self):
        # Deliberately leave the user's tab, login state and browser open.
        self.page = None
        self.registry = {}
        self.png = None
