import asyncio,json,os,tempfile,time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parent
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'.tools/browsers')
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'.runtime/tmp')
from playwright.async_api import async_playwright


async def main():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8765',trust_env=False) as api:
        api.headers['x-privacy-session']=(await api.get('/api/bootstrap')).json()['token']
        for _ in range(60):
            if not (await api.get('/api/status')).json()['initializing']:break
            await asyncio.sleep(1)
        pairing=(await api.get('/api/extension/pair-code')).json()
        if pairing['connected']:
            raise SystemExit('Close the connected side panel before running this isolated integration test.')
        code=pairing['code']
        async with async_playwright() as p:
            profile=tempfile.mkdtemp(prefix='extension-test-',dir=ROOT/'.runtime')
            ext=ROOT/'extension'
            context=await p.chromium.launch_persistent_context(profile,headless=False,no_viewport=True,ignore_default_args=['--disable-extensions'],args=[f'--disable-extensions-except={ext}',f'--load-extension={ext}','--window-size=1440,1000'])
            try:
                worker=context.service_workers[0] if context.service_workers else await context.wait_for_event('serviceworker')
                extension_id=worker.url.split('/')[2]
                panel=await context.new_page()
                errors=[]
                panel.on('pageerror',lambda e:errors.append(str(e)))
                await panel.goto(f'chrome-extension://{extension_id}/panel.html')
                await panel.locator('#pair-code').fill(code)
                await panel.locator('#pair').click()
                await panel.locator('#workspace').wait_for(state='visible',timeout=15000)
                target=await context.new_page()
                await target.goto('http://127.0.0.1:8766/scenario/authentication')
                await target.locator('#email').fill('person1@example.test')
                await target.locator('#password').fill('DemoOnly!1Private')
                await target.locator('#otp').fill('482913')
                await target.evaluate("sessionStorage.setItem('manual-session','retained')")
                await panel.evaluate("document.getElementById('provider').value='demo';document.getElementById('prompt').value='Sign in using the fields I filled manually.';document.getElementById('start').click()")
                result=None
                for _ in range(100):
                    status=(await api.get('/api/status')).json();run=status.get('run')
                    if run and run['scenario']=='authentication' and run['status'] not in ('starting','running','awaiting_approval'):
                        result=run;break
                    await asyncio.sleep(.5)
                if not result or result['status']!='completed':
                    print(json.dumps({'failure':result and {k:result[k] for k in ['status','error','steps','events']},'panel_error':await panel.locator('#error').inner_text()}))
                    raise AssertionError('Real extension manual-login task did not complete')
                assert await target.evaluate("sessionStorage.getItem('manual-session')")=='retained'
                assert not target.is_closed()
                # Pause a new task without closing or navigating the existing tab.
                await target.goto('http://127.0.0.1:8766/scenario/checkout')
                await target.locator('#name').fill('Manual test value')
                await panel.evaluate("document.getElementById('prompt').value='Fill the checkout fields.';document.getElementById('start').click()")
                await asyncio.sleep(.3)
                await panel.evaluate("document.getElementById('pause').click()")
                for _ in range(50):
                    r=(await api.get('/api/status')).json()['run']
                    if r['status']=='paused':break
                    await asyncio.sleep(.2)
                assert r['status']=='paused'
                assert not target.is_closed()
                await target.locator('#name').fill('User can edit after pause')
                assert await target.locator('#name').input_value()=='User can edit after pause'
                await panel.evaluate("document.querySelector('[data-view=privacy]').click();document.getElementById('inspect').click()")
                await panel.locator('#preview').wait_for(state='visible',timeout=30000)
                assert (await panel.locator('#preview').get_attribute('src')).startswith('data:image/png;base64,')
                # Stop clears local values without closing the user's actual page.
                await panel.evaluate("document.getElementById('stop').click()")
                await asyncio.sleep(1)
                assert not target.is_closed()
                assert not errors, errors
                report={'transport':'Real installed MV3 extension + chrome.debugger + paired localhost WebSocket','manual_login':'verified signin with prefilled values; no demo vault','session_preserved':True,'pause_keeps_tab_interactive':True,'local_inspection':True,'stop_keeps_tab_open':True,'model':'deterministic local driver, not AI','errors':errors}
                (ROOT/'docs/extension-integration-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                print(json.dumps(report),flush=True)
            finally:
                await context.close()

asyncio.run(main())
