import pytest
from backend.browser import Browser, launch_options
from backend.privacy import Detector, PrivacyError
from backend.contracts import Action


@pytest.fixture
async def browser():
    from playwright.async_api import async_playwright

    d = Detector()
    d.status.update(presidio=True, ocr=True)
    # Security-boundary tests use a detector stub; real detector integration is benchmarked separately.
    d.visual_boxes = lambda png: []
    b = Browser(d)
    b.pw = await async_playwright().start()
    b.browser = await b.pw.chromium.launch(**launch_options(b.pw))
    b.page = await b.browser.new_page(viewport={"width": 1280, "height": 900})
    await b.page.set_content(
        '<label>Email<input aria-label="Email address"></label><button>Send reply</button><p>person@example.test</p>'
    )
    b.origin = b.get_origin(b.page.url)
    await b.capture()
    yield b
    await b.close()


async def test_stale_snapshot_blocked(browser):
    with pytest.raises(PrivacyError):
        await browser.validate(Action(type="done", snapshot_id="old"))


async def test_mutated_page_blocked(browser):
    await browser.page.locator("button").evaluate(
        "e=>e.textContent='Different operation'"
    )
    with pytest.raises(PrivacyError):
        await browser.validate(Action(type="done", snapshot_id=browser.snapshot))


async def test_guessed_target_blocked(browser):
    with pytest.raises(PrivacyError):
        await browser.validate(
            Action(type="click", snapshot_id=browser.snapshot, target_id="madeup")
        )


async def test_public_fill_cannot_write_secret_field(browser):
    target = next(k for k, v in browser.registry.items() if v["tag"] == "input")
    with pytest.raises(PrivacyError):
        await browser.execute(
            Action(
                type="fill_public",
                snapshot_id=browser.snapshot,
                target_id=target,
                text="anything",
            )
        )


async def test_disabled_target_after_capture(browser):
    target = next(k for k, v in browser.registry.items() if v["tag"] == "button")
    await browser.page.locator("button").evaluate("e=>e.disabled=true")
    with pytest.raises(PrivacyError):
        await browser.execute(
            Action(type="click", snapshot_id=browser.snapshot, target_id=target)
        )


async def test_duplicate_handle(browser):
    target = next(k for k, v in browser.registry.items() if v["tag"] == "button")
    await browser.page.locator("button").evaluate("e=>e.after(e.cloneNode(true))")
    with pytest.raises(PrivacyError):
        await browser.execute(
            Action(type="click", snapshot_id=browser.snapshot, target_id=target)
        )


async def test_missing_detector_fails_closed(browser):
    browser.detector.status["ocr"] = False
    with pytest.raises(PrivacyError):
        await browser.capture()


async def test_snapshot_hides_local_values_and_urls(browser):
    p = await browser.capture()
    import json

    text = json.dumps(p["observation"])
    assert "person@example.test" not in text
    assert "value" not in text and "href" not in text


async def test_password_reveal_button_is_not_a_secret_field(browser):
    await browser.page.locator("button").evaluate("e=>e.textContent='Show password'")
    p = await browser.capture()
    button = next(c for c in p["observation"]["controls"] if c["role"] == "button")
    assert button["purpose"] is None


async def test_submit_input_has_human_label_and_cannot_be_filled(browser):
    await browser.page.set_content(
        '<input type="submit" name="login-button" value="Login">'
    )
    p = await browser.capture()
    c = p["observation"]["controls"][0]
    assert c["label"] == "Login"
    with pytest.raises(PrivacyError):
        await browser.execute(
            Action(
                type="fill_public",
                snapshot_id=browser.snapshot,
                target_id=c["id"],
                text="anything",
            )
        )


async def test_declined_approval_blocks(browser):
    import asyncio
    from backend.agent import Run, Gateway
    from backend.contracts import StartRequest

    run = Run(
        StartRequest(scenario="developer"),
        browser,
        Gateway(browser.detector),
        {},
        browser.page.url,
    )
    action = Action(type="done", snapshot_id=browser.snapshot)
    task = asyncio.create_task(run.ask("action", action, "Confirm test action"))
    await asyncio.sleep(0.01)
    assert run.status == "awaiting_approval" and not task.done()
    run.pending = False
    run.decision.set()
    with pytest.raises(PrivacyError, match="declined"):
        await task


async def test_approval_invalidated_by_page_change(browser):
    import asyncio
    from backend.agent import Run, Gateway
    from backend.contracts import StartRequest

    run = Run(
        StartRequest(scenario="developer"),
        browser,
        Gateway(browser.detector),
        {},
        browser.page.url,
    )
    task = asyncio.create_task(
        run.ask(
            "action",
            Action(type="done", snapshot_id=browser.snapshot),
            "Confirm test action",
        )
    )
    await asyncio.sleep(0.01)
    await browser.page.locator("button").evaluate(
        "e=>e.textContent='Different operation'"
    )
    run.pending = True
    run.decision.set()
    with pytest.raises(PrivacyError, match="Stale"):
        await task


async def test_progressive_disclosure_sends_only_sanitized_crop_after_approval(browser):
    import asyncio
    from backend.agent import Run
    from backend.contracts import StartRequest

    await browser.page.locator("button").evaluate(
        "e=>{e.textContent='Mute microphone';e.onclick=()=>window.fixtureOutcome='mute'}"
    )

    async def existing_page(*a, **kw):
        pass

    browser.open = existing_page

    class ScriptedPlanner:
        last_receipt = None

        def __init__(self):
            self.detector = browser.detector
            self.calls = []

        async def plan(self, obs, task, refs, known, provider, image=None):
            self.calls.append(image)
            if image is None:
                a = Action(
                    type="request_context",
                    snapshot_id=obs["snapshot_id"],
                    region_id=obs["regions"][0]["id"],
                )
            else:
                assert image == browser.png
                target = next(c["id"] for c in obs["controls"] if c["role"] == "button")
                a = Action(
                    type="click", snapshot_id=obs["snapshot_id"], target_id=target
                )
            return a, {
                "digest": "synthetic-receipt",
                "bytes": 100,
                "destination": "Scripted test planner",
            }

    planner = ScriptedPlanner()
    run = Run(
        StartRequest(scenario="conference", provider="gemini"),
        browser,
        planner,
        {},
        browser.page.url,
    )
    task = asyncio.create_task(run.loop(browser.page.url))
    for _ in range(100):
        if run.approval:
            break
        await asyncio.sleep(0.05)
    assert run.approval and planner.calls == [None]
    assert run.approval["kind"] == "disclosure"
    run.pending = True
    run.decision.set()
    await asyncio.wait_for(task, 15)
    assert run.status == "completed" and run.outcome == "mute"
    assert len(planner.calls) == 2 and planner.calls[1] is not None
    assert any(r.get("image_disclosed") for r in run.receipts)
