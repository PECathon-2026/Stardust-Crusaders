"""Launch a visible, separate Chromium profile with the unpacked extension.

This is a genuine browser extension. The dedicated profile does not access the
user's everyday browser cookies or saved passwords. Existing Chrome/Edge users
can instead load extension/ through their browser's extension management page.
"""
import asyncio
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(ROOT / '.tools' / 'browsers')
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT / '.runtime' / 'tmp')
from playwright.async_api import async_playwright


async def main():
    extension = ROOT / 'extension'
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(ROOT / '.runtime' / 'extension-profile'),
            headless=False, no_viewport=True,
            ignore_default_args=['--disable-extensions'],
            args=[f'--disable-extensions-except={extension}', f'--load-extension={extension}', '--window-size=1440,1000'],
        )
        worker = context.service_workers[0] if context.service_workers else await context.wait_for_event('serviceworker')
        extension_id = worker.url.split('/')[2]
        (ROOT / '.runtime' / 'extension-browser.json').write_text(json.dumps({'extension_id':extension_id,'profile':str(ROOT / '.runtime' / 'extension-profile')}),encoding='utf-8')
        page = await context.new_page()
        await page.goto(f'chrome-extension://{extension_id}/welcome.html')
        await page.get_by_role('button',name='Open PrivacyLens side panel').click()
        print('PrivacyLens browser and side panel opened.', flush=True)
        done = asyncio.Event()
        context.on('close', lambda _: done.set())
        await done.wait()


if __name__ == '__main__':
    asyncio.run(main())
