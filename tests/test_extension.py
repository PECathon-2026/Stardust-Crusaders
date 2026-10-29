import asyncio
import importlib
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.extension_api import tab_scenario, PAIR_CODE, PAIRED_ORIGINS, PAIR_ATTEMPTS
from backend.extension_transport import ExtensionRPC, ExtensionBrowser
from backend.privacy import Detector, PrivacyError

state = importlib.import_module('backend.app')
ORIGIN = 'chrome-extension://' + 'a' * 32


@pytest.fixture(autouse=True)
def clear_pairing():
    PAIRED_ORIGINS.clear()
    PAIR_ATTEMPTS.clear()
    yield
    PAIRED_ORIGINS.clear()
    PAIR_ATTEMPTS.clear()


def test_extension_pairing_requires_explicit_local_code():
    client = TestClient(state.app)
    headers = {'origin':ORIGIN,'sec-fetch-site':'cross-site'}
    assert client.get('/api/status',headers={**headers,'x-privacy-session':state.token}).status_code == 403
    assert client.post('/api/extension/pair',headers=headers,json={'code':'wrong'}).status_code == 403
    response = client.post('/api/extension/pair',headers=headers,json={'code':PAIR_CODE})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == ORIGIN
    assert response.json()['token'] == state.token
    assert client.get('/api/status',headers={**headers,'x-privacy-session':state.token}).status_code == 200
    assert client.get('/api/status',headers=headers).status_code == 401


def test_ordinary_website_cannot_pair():
    response = TestClient(state.app).post('/api/extension/pair',headers={'origin':'https://attacker.invalid'},json={'code':PAIR_CODE})
    assert response.status_code == 403
    assert not PAIRED_ORIGINS


def test_pairing_is_rate_limited_and_preflight_is_narrow():
    client=TestClient(state.app)
    for _ in range(5):
        assert client.post('/api/extension/pair',headers={'origin':ORIGIN},json={'code':'wrong'}).status_code==403
    assert client.post('/api/extension/pair',headers={'origin':ORIGIN},json={'code':PAIR_CODE}).status_code==429
    assert client.options('/api/extension/pair',headers={'origin':ORIGIN}).status_code==200
    assert client.options('/api/settings',headers={'origin':ORIGIN}).status_code==403


@pytest.mark.parametrize('url', ['https://en.wikipedia.org/wiki/Main_Page','http://127.0.0.1:8765/','file:///C:/secret','https://www.saucedemo.com.evil.invalid/','https://user:pass@www.saucedemo.com/','http://127.0.0.1:8766/scenario/authentication?next=evil','https://www.saucedemo.com/?redirect=evil'])
def test_unapproved_tab_rejected(url):
    with pytest.raises(HTTPException):tab_scenario(url)


def test_current_inventory_and_demo_tab_supported():
    assert tab_scenario('https://www.saucedemo.com/inventory.html')=='saucedemo'
    assert tab_scenario('http://127.0.0.1:8766/scenario/support?seed=9&layout=1')=='support'


async def test_rpc_ignores_unrelated_replies_and_disconnects_safely():
    messages=[]
    class Socket:
        async def send_json(self,message):messages.append(message)
    rpc=ExtensionRPC(Socket())
    task=asyncio.create_task(rpc.call('evaluate',expression='location.href'))
    await asyncio.sleep(0)
    rpc.receive({'id':'invented','ok':True,'result':'unsafe'})
    assert not task.done()
    rpc.disconnect()
    with pytest.raises(PrivacyError,match='disconnected'):await task
    assert not rpc.pending


async def test_closing_extension_adapter_does_not_close_user_tab():
    class RPC:
        async def call(self,*args,**kwargs):pytest.fail('Closing must not send browser commands')
    browser=ExtensionBrowser(Detector(),RPC(),'https://www.saucedemo.com/')
    browser.registry={'target':{'value':'local-secret'}}
    await browser.close()
    assert browser.registry=={} and browser.page is None
