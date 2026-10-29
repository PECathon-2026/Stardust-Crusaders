import asyncio, hashlib, json, secrets
from pathlib import Path
from urllib.parse import urlparse
from .privacy import PrivacyError, StaleObservation, redact_image, image_url


def launch_options(playwright, headless=True):
    options = {"headless": headless}
    if not Path(playwright.chromium.executable_path).exists():
        edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
        if edge.exists():
            options["channel"] = "msedge"
    return options


COLLECT = r"""() => {
 const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth};
 for(const e of document.querySelectorAll('[data-pl-target]'))e.removeAttribute('data-pl-target');
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const controls=[]; let i=0;
 for(const e of document.querySelectorAll('button,a,input:not([type=hidden]),textarea,select,[role=button]')){
  if(!visible(e))continue;
  const id='e_'+Array.from(crypto.getRandomValues(new Uint8Array(16)),v=>v.toString(16).padStart(2,'0')).join('');e.setAttribute('data-pl-target',id);
  let label=e.getAttribute('aria-label')||e.labels?.[0]?.innerText||e.innerText||(['submit','button','reset'].includes(e.type)?e.value:'')||e.getAttribute('placeholder')||e.name||e.id||e.tagName;
  const product=e.closest('.inventory_item')?.querySelector('.inventory_item_name')?.textContent;
  if(product&&e.tagName==='BUTTON')label+=' — '+product;
  if(e.classList.contains('shopping_cart_link'))label='Shopping cart';
  controls.push({id,label:label.slice(0,300),tag:e.tagName.toLowerCase(),type:e.type||'',autocomplete:e.autocomplete||'',name:e.name||e.id||'',value:e.value||'',disabled:!!e.disabled,rect:rect(e),href:e.tagName==='A'?e.href:null,options:e.tagName==='SELECT'?Array.from(e.options).slice(0,50).map(o=>({label:o.label.slice(0,300),selected:o.selected,disabled:o.disabled})):[]});
 }
 const texts=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
 while(n=walker.nextNode()){
  const e=n.parentElement;if(!e||e.closest('script,style,noscript,option')||!visible(e)||!n.textContent.trim())continue;
  const range=document.createRange();range.selectNodeContents(n);
  const boxes=Array.from(range.getClientRects()).map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}));
  const scope=e.closest('section,[aria-label]');
  texts.push({node_index:texts.length,trim_start:n.textContent.length-n.textContent.trimStart().length,text:n.textContent.trim().slice(0,3000),context:(scope?.getAttribute('aria-label')||'')+' '+(e.getAttribute('aria-label')||''),boxes});
 }
 const media=Array.from(document.querySelectorAll('img,canvas,video,iframe,[role=img]')).filter(visible).map(e=>({...rect(e),tag:e.tagName.toLowerCase(),private:/private|participant|medical/i.test((e.closest('section,[aria-label]')?.getAttribute('aria-label')||'')+' '+(e.getAttribute('aria-label')||'')),kind:'MEDIA',source:'conservative-media'}));
 const regions=Array.from(document.querySelectorAll('section')).filter(visible).map((e,j)=>({id:'r'+j,label:e.querySelector('h2')?.innerText||'Page section',...rect(e)}));
 if(!regions.length)regions.push({id:'r0',label:'Current viewport',x:0,y:0,width:innerWidth,height:innerHeight});
 return {controls,texts,media,regions,width:innerWidth,height:innerHeight,title:document.title};
}"""
FINGERPRINT = r"""() => JSON.stringify({url:location.href,text:document.body.innerText,fields:Array.from(document.querySelectorAll('input,textarea,select')).map(e=>[e.value,e.type,e.disabled]),controls:Array.from(document.querySelectorAll('[data-pl-target]')).map(e=>{const r=e.getBoundingClientRect();return[e.getAttribute('data-pl-target'),e.getAttribute('aria-label'),e.name,e.type,e.disabled,e.href,r.x,r.y,r.width,r.height]}),scroll:[scrollX,scrollY],size:[innerWidth,innerHeight]})"""

TEXT_SPAN_BOXES = r"""({index,start,end}) => {
 const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth};
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n,i=0;
 while(n=walker.nextNode()){
  const e=n.parentElement;if(!e||e.closest('script,style,noscript,option')||!visible(e)||!n.textContent.trim())continue;
  if(i++!==index)continue;
  if(start<0||end>n.textContent.length||end<=start)return [];
  const range=document.createRange();range.setStart(n,start);range.setEnd(n,end);
  return Array.from(range.getClientRects()).map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}));
 }return [];
}"""

PUBLIC_LABELS = {
    'https://en.wikipedia.org': ('Wikipedia', 'The Free Encyclopedia', 'Wikimedia Foundation'),
    'https://www.saucedemo.com': ('Swag Labs', 'Sauce Labs Backpack', 'Sauce Labs Bike Light', 'Sauce Labs Bolt T-Shirt', 'Sauce Labs Fleece Jacket', 'Sauce Labs Onesie', 'Test.allTheThings() T-Shirt (Red)'),
}


def purpose(control):
    s = (
        " ".join(
            str(control.get(k, "")) for k in ["label", "type", "autocomplete", "name"]
        )
    ).lower()
    for key, words in [
        ("cvv", ["cvv", "cc-csc", "security code"]),
        ("card", ["card number", "cc-number"]),
        ("otp", ["one-time", "otp", "verification code"]),
        ("password", ["password"]),
        ("email", ["email"]),
        ("address", ["address", "street-address"]),
        ("name", ["full name", "first name", "last name"]),
        ("username", ["username", "user name"]),
    ]:
        if any(w in s for w in words):
            return key
    return None


class Browser:
    def __init__(self, detector):
        self.detector = detector
        self.pw = None
        self.browser = None
        self.page = None
        self.registry = {}
        self.snapshot = None
        self.fingerprint = None
        self.png = None
        self.regions = []
        self.origin = ""

    async def open(self, url, headless=True):
        from playwright.async_api import async_playwright

        await self.close()
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            **launch_options(self.pw, headless)
        )
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
            service_workers="block",
        )
        self.page = await context.new_page()
        self.origin = self.get_origin(url)

        async def route_handler(route):
            parsed = urlparse(route.request.url)
            if (
                parsed.hostname in ("localhost", "127.0.0.1", "::1")
                and parsed.port != 8766
            ):
                await route.abort()
                return
            if (
                route.request.is_navigation_request()
                and self.get_origin(route.request.url) != self.origin
            ):
                await route.abort()
                return
            await route.continue_()

        await context.route("**/*", route_handler)
        await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await self.page.wait_for_timeout(300)

    @staticmethod
    def get_origin(url):
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    async def signature(self):
        return hashlib.sha256(
            (await self.page.evaluate(FINGERPRINT)).encode()
        ).hexdigest()

    async def verified_external_outcome(self, scenario):
        path = urlparse(self.page.url).path
        if scenario == "wikipedia" and path == "/wiki/Privacy":
            if (
                await self.page.locator("h1").count()
                and (await self.page.locator("h1").first.inner_text()).strip()
                == "Privacy"
            ):
                return "article_verified"
        if scenario == "saucedemo" and path == "/cart.html":
            names = await self.page.locator(".inventory_item_name").all_text_contents()
            if names == ["Sauce Labs Backpack"]:
                return "cart_verified"
        return None

    async def capture(self, known=(), mode="contract"):
        started = __import__("time").perf_counter()
        if not self.page:
            raise PrivacyError("Browser is not running")
        for attempt in range(2):
            raw = await self.page.evaluate(COLLECT)
            before = await self.signature()
            png = await self.page.screenshot(type="png", animations="disabled")
            after = await self.signature()
            if before == after:
                break
            await self.page.wait_for_timeout(750)
        else:
            raise PrivacyError("Page changed while capturing")
        if not self.detector.status["presidio"] or not self.detector.status["ocr"]:
            raise PrivacyError("Required local detectors are unavailable")
        masks = [m for m in raw["media"] if m['tag'] != 'img' or m['private'] or not self.detector.status.get('faces')]
        findings = []
        texts = []
        controls = []
        self.registry = {}
        # Explicit public demo product dictionary; never exempts regex secrets or vault values.
        public_literals = PUBLIC_LABELS.get(self.origin, ())
        for item in raw["texts"]:
            private = any(
                w in item["context"].lower()
                for w in ["private", "participant", "medical"]
            )
            if private:
                safe = "[REDACTED:PRIVATE_CONTENT]"
                fs = []
                for box in item["boxes"]:
                    masks.append(
                        {**box, "kind": "PRIVATE_CONTENT", "source": "container-policy"}
                    )
                findings.append(
                    {
                        "kind": "PRIVATE_CONTENT",
                        "source": "container-policy",
                        "reason": "Protected content region",
                    }
                )
            else:
                safe, fs = self.detector.sanitize(item["text"], known, public_literals)
                if fs:
                    for finding in fs:
                        # Python offsets count Unicode points; DOM Range uses UTF-16.
                        start = item['trim_start'] + len(item['text'][:finding.start].encode('utf-16-le')) // 2
                        end = item['trim_start'] + len(item['text'][:finding.end].encode('utf-16-le')) // 2
                        boxes = await self.page.evaluate(TEXT_SPAN_BOXES, {'index':item['node_index'], 'start':start, 'end':end})
                        for box in boxes or item['boxes']:
                            masks.append({**box, "kind": finding.kind, "source": "dom-text"})
                    findings.extend(
                        {"kind": f.kind, "source": f.source, "reason": f.reason}
                        for f in fs
                    )
            texts.append(safe)
        for c in raw["controls"]:
            p = purpose(c) if c["tag"] in ("input", "textarea") else None
            label, fs = self.detector.sanitize(c["label"], known, public_literals)
            if c["tag"] in ("input", "textarea") and c["type"] not in (
                "submit",
                "button",
                "reset",
                "checkbox",
                "radio",
            ) and (p or c['type'] == 'password' or self.detector.sanitize(c.get('value', ''), known)[1]):
                masks.append(
                    {
                        **c["rect"],
                        "kind": p.upper() if p else "INPUT",
                        "source": "structural",
                    }
                )
                findings.append(
                    {
                        "kind": p.upper() if p else "INPUT",
                        "source": "structural",
                        "reason": "Sensitive input value stays local",
                    }
                )
            # Real hrefs, values and local selectors never enter observation.
            self.registry[c["id"]] = {**c, "purpose": p, "safe_label": label}
            role = "button" if c["type"] in ("submit", "button", "reset") else c["tag"]
            controls.append(
                {
                    "id": c["id"],
                    "role": role,
                    "label": label,
                    "purpose": p,
                    "filled": bool(c["value"]),
                    "disabled": c["disabled"],
                }
            )
            if c["tag"] == "select":
                controls[-1]["options"] = [
                    {"label": self.detector.sanitize(option["label"], known)[0],
                     "selected": option["selected"], "disabled": option["disabled"]}
                    for option in c.get("options", [])
                ]
        visual = await asyncio.to_thread(self.detector.visual_boxes, png, known=known, public_literals=public_literals)
        if await self.signature() != after:
            raise StaleObservation("Page changed while applying privacy masks")
        masks.extend(visual)
        findings.extend(
            {"kind": b["kind"], "source": b["source"], "reason": "Local pixel detector"}
            for b in visual
        )
        self.png = redact_image(png, masks)
        self.snapshot = "s_" + secrets.token_hex(12)
        self.fingerprint = after
        self.regions = raw["regions"]
        safe_regions = [
            {"id": r["id"], "label": self.detector.sanitize(r["label"], known)[0]}
            for r in self.regions
        ]
        full = "\n".join(texts)[:16000]
        # Contract view sends controls + short public status. Additional context is explicit.
        minimal = "\n".join(
            t
            for t in texts
            if any(
                w in t.lower()
                for w in [
                    "successfully",
                    "submitted",
                    "muted",
                    "revoked",
                    "order placed",
                    "required fields",
                    "invalid",
                    "please select",
                ]
            )
        )[:1000]
        path = urlparse(self.page.url).path
        page_state = (
            "cart"
            if path == "/cart.html"
            else "inventory"
            if path == "/inventory.html"
            else "privacy-article"
            if path == "/wiki/Privacy"
            else "current-task-page"
        )
        obs = {
            "snapshot_id": self.snapshot,
            "page": page_state,
            "controls": controls,
            "context": full if mode == "baseline" else minimal,
            "regions": safe_regions,
        }
        if public_literals:
            obs["public_literals"] = list(public_literals)
        return {
            "observation": obs,
            "original": image_url(png),
            "sanitized": image_url(self.png),
            "findings": findings,
            "masks": masks,
            "full_context": full,
            "latency_ms": round((__import__("time").perf_counter() - started) * 1000),
            "raw_text_bytes": len(full.encode()),
            "disclosed_text_bytes": len(obs["context"].encode()),
        }

    async def validate(self, action):
        if (
            action.snapshot_id != self.snapshot
            or await self.signature() != self.fingerprint
        ):
            raise StaleObservation("Stale observation: capture again before acting")
        if self.get_origin(self.page.url) != self.origin:
            raise PrivacyError("Origin changed")
        if action.target_id:
            c = self.registry.get(action.target_id)
            if not c:
                raise PrivacyError("Unknown target")
            target = self.page.locator(f'[data-pl-target="{action.target_id}"]')
            if (
                await target.count() != 1
                or not await target.is_visible()
                or not await target.is_enabled()
            ):
                raise PrivacyError("Target is unavailable")
            if action.type in ("fill_public", "fill_secret") and (
                c["tag"] not in ("input", "textarea")
                or c["type"]
                in ("submit", "button", "reset", "checkbox", "radio", "file")
            ):
                raise PrivacyError("Target is not a text field")
            if action.type == "select" and c["tag"] != "select":
                raise PrivacyError("Target is not a select")
            if c.get("href") and self.get_origin(c["href"]) != self.origin:
                raise PrivacyError("External navigation denied")
            return c, target
        return None, None

    async def execute(self, action, secret=None):
        c, target = await self.validate(action)
        if action.type == "click":
            await target.click(timeout=5000)
        elif action.type == "fill_public":
            if c["purpose"]:
                raise PrivacyError("Sensitive fields require local secret permission")
            await target.fill(action.text, timeout=5000)
        elif action.type == "fill_secret":
            await target.fill(secret, timeout=5000)
        elif action.type == "select":
            await target.select_option(label=action.text, timeout=5000)
        elif action.type == "scroll":
            await self.page.mouse.wheel(0, 500 if action.direction == "down" else -500)
        elif action.type == "wait":
            await self.page.wait_for_timeout(300)
        await self.page.wait_for_timeout(150)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
        self.browser = None
        self.page = None
        self.pw = None
        self.registry = {}
        self.png = None
