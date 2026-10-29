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
    d.visual_boxes = lambda png, **kwargs: []
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


async def test_custom_prompt_does_not_stop_at_preset_outcome(browser):
    from backend.agent import Run
    from backend.contracts import StartRequest
    await browser.page.evaluate("window.fixtureOutcome='mute'")
    async def existing_page(*args, **kwargs): pass
    browser.open = existing_page
    class Planner:
        last_receipt = None
        calls = 0
        async def plan(self, obs, task, refs, known, provider):
            self.calls += 1
            assert task == 'Inspect the meeting controls and stop.'
            return Action(type='done', snapshot_id=obs['snapshot_id']), {'bytes':0, 'destination':'Test planner'}
    planner = Planner()
    run = Run(StartRequest(scenario='conference',provider='gemini',task='Inspect the meeting controls and stop.',verify_scenario_outcome=False),browser,planner,{},browser.page.url)
    await run.loop(browser.page.url)
    assert planner.calls == 1
    assert run.status == 'needs_review'
    assert run.outcome == 'planner_finished'


async def test_transient_capture_change_is_recaptured_before_planning(browser):
    from backend.agent import Gateway, Run
    from backend.contracts import StartRequest
    from backend.privacy import StaleObservation
    await browser.page.set_content('<button onclick="window.fixtureOutcome=\'mute\'">Mute microphone</button>')
    async def existing_page(*args, **kwargs):pass
    browser.open=existing_page
    capture=browser.capture
    count=0
    async def changing_once(*args,**kwargs):
        nonlocal count
        count+=1
        if count==1:raise StaleObservation('Page changed')
        return await capture(*args,**kwargs)
    browser.capture=changing_once
    gateway=Gateway(browser.detector)
    run=Run(StartRequest(scenario='conference',provider='demo'),browser,gateway,{},browser.page.url)
    await run.loop(browser.page.url)
    assert run.status=='completed' and count==3 and gateway.sent==0
    assert any(e['title']=='Page still changing' for e in run.events)


async def test_select_observation_has_sanitized_choices_and_selection(browser):
    await browser.page.set_content('<select aria-label="Category"><option>Choose category</option><option selected>Billing</option><option>person@example.test</option></select><p>Please complete the required fields correctly.</p>')
    preview = await browser.capture()
    observation = preview["observation"]
    options = observation["controls"][0]["options"]
    assert options[1] == {"label": "Billing", "selected": True, "disabled": False}
    assert "person@example.test" not in str(observation)
    assert "required fields" in observation["context"]


async def test_repeated_no_progress_action_stops_before_third_click(browser):
    from backend.agent import Run
    from backend.contracts import StartRequest
    await browser.page.set_content('<button onclick="window.clicks=(window.clicks||0)+1">Open details</button>')
    async def existing_page(*args, **kwargs):
        pass
    browser.open = existing_page
    class RepeatingPlanner:
        last_receipt = None
        detector = browser.detector
        async def plan(self, obs, *args):
            return Action(type="click", snapshot_id=obs["snapshot_id"], target_id=obs["controls"][0]["id"]), {"digest": "test", "bytes": 0}
    run = Run(StartRequest(scenario="developer", provider="gemini"), browser, RepeatingPlanner(), {}, browser.page.url)
    await run.loop(browser.page.url)
    assert run.status == "blocked"
    assert "without observable progress" in run.error
    assert await browser.page.evaluate('window.clicks') == 2


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


async def test_public_product_image_preserved_private_media_stays_masked(browser):
    browser.detector.status['faces'] = True
    await browser.page.set_content('<img style="width:100px;height:100px" alt="Product" src="data:image/svg+xml,%3Csvg xmlns=\"http://www.w3.org/2000/svg\"/%3E"><section aria-label="Private conversation"><img style="width:100px;height:100px" alt="Private photo"></section>')
    preview = await browser.capture()
    media = [b for b in preview['masks'] if b['source']=='conservative-media']
    assert len(media) == 1 and media[0]['private']
    browser.detector.status['faces'] = False
    preview = await browser.capture()
    assert len([b for b in preview['masks'] if b['source']=='conservative-media']) == 2


async def test_sensitive_span_does_not_hide_surrounding_public_text(browser):
    await browser.page.set_content('<p style="font:20px monospace">Public product information: person@example.test — available today</p>')
    line = await browser.page.locator('p').bounding_box()
    preview = await browser.capture(mode='baseline')
    boxes = [b for b in preview['masks'] if b['source']=='dom-text']
    assert boxes and all(b['width'] < line['width']/2 for b in boxes)
    assert 'Public product information' in preview['observation']['context']
    assert 'person@example.test' not in preview['observation']['context']


async def test_public_search_is_visible_but_private_input_remains_masked(browser):
    await browser.page.set_content('<input type="search" aria-label="Search Wikipedia" value="Privacy"><input type="password" aria-label="Password" value="secret-value">')
    preview = await browser.capture()
    boxes = [b for b in preview['masks'] if b['source']=='structural']
    assert len(boxes) == 1 and boxes[0]['kind']=='PASSWORD'
    await browser.page.locator('input[type=search]').fill('person@example.test')
    preview = await browser.capture()
    assert len([b for b in preview['masks'] if b['source']=='structural']) == 2


async def test_public_profile_keeps_private_medical_container_protected(browser):
    await browser.page.set_content('<main><article>Public product facts</article><section aria-label="Private medical record"><span aria-label="Details">Patient fictional diagnosis</span></section></main>')
    preview=await browser.capture(mode='baseline',privacy_profile='public')
    assert 'Public product facts' in preview['observation']['context']
    assert 'Patient fictional diagnosis' not in preview['observation']['context']
    assert preview['observation']['privacy_profile']=='public'


async def test_public_article_link_name_is_preserved_but_private_name_is_not(browser,monkeypatch):
    from backend.privacy import Finding
    def detect(text,*args,**kwargs):
        return [Finding('PERSON',text.index('Ada Lovelace'),text.index('Ada Lovelace')+12,'presidio','test')] if 'Ada Lovelace' in text else []
    monkeypatch.setattr(browser.detector,'detect',detect)
    await browser.page.set_content('<article><a>Ada Lovelace</a></article><section aria-label="Private patient"><button>Ada Lovelace</button></section>')
    preview=await browser.capture(privacy_profile='public')
    controls=preview['observation']['controls']
    assert controls[0]['label']=='Ada Lovelace'
    assert 'Ada Lovelace' not in controls[1]['label']


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
