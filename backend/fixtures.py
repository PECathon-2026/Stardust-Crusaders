"""Synthetic fixtures; annotations are returned separately, never embedded as detector hints."""

import html
from faker import Faker


def values(seed=1):
    f = Faker("en_IN")
    f.seed_instance(seed)
    return {
        "name": f.name(),
        "address": f"{12 + seed} Example Lane, Pune 411001",
        "card": "4111 1111 1111 1111",
        "cvv": "737",
        "email": f"person{seed}@example.test",
        "password": f"DemoOnly!{seed}Private",
        "otp": "482913",
        "phone": f"+91 98765 {10000 + seed:05d}",
        "pan": "ABCDE1234F",
        "api_key": "ghp_" + "aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4",
        "ip": "192.168.42.17",
        "message": f"Private: my medical appointment is on Friday. Patient reference {seed}.",
        "username": "standard_user",
        "sauce_password": "secret_sauce",
    }


STYLE = """*{box-sizing:border-box}body{margin:0;background:#f5f5f1;color:#172c2b;font:16px Arial,sans-serif}header{background:#113e38;color:white;padding:24px 48px;display:flex;justify-content:space-between}main{padding:35px 48px;max-width:1180px;margin:auto}section{background:white;border:1px solid #dce3df;border-radius:16px;padding:25px;margin:18px 0}h1{font-size:32px}h2{font-size:21px}label{display:block;font-size:14px;margin:16px 0 6px}input,select,textarea{padding:12px;border:1px solid #b7c6bf;border-radius:8px;width:100%;font-size:16px}button{background:#155e50;color:white;border:0;border-radius:8px;padding:13px 20px;margin:16px 8px 0 0;font-weight:bold;cursor:pointer}button.secondary{background:#e9f1ed;color:#16433c}.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:24px}.tag{font-size:12px;background:#e7f1e9;color:#245348;padding:6px 10px;border-radius:20px}.muted{color:#677c76;line-height:1.7}.tile{height:210px;background:linear-gradient(140deg,#315c68,#d9b5a3);display:flex;align-items:center;justify-content:center;font-size:72px;border-radius:12px}.row{display:flex;gap:20px}.row>*{flex:1}code{font-size:15px;overflow-wrap:anywhere}#result{padding:18px;background:#e3f5e7;border-radius:12px;margin-top:18px}body.variant .grid{grid-template-columns:1fr 1.4fr}body.variant section{border-radius:4px}body.variant{background:#eaf0f6}"""


def fixture(scenario, seed=1, layout=0):
    v = values(seed)
    e = lambda k: html.escape(v[k])
    truth = []

    def field(label, purpose, autocomplete="", typ="text"):
        return f'<label for="{purpose}">{label}</label><input id="{purpose}" name="{purpose}" type="{typ}" autocomplete="{autocomplete}" aria-label="{label}">'

    if scenario == "checkout":
        truth = [
            ("PERSON", v["name"]),
            ("ADDRESS", v["address"]),
            ("CREDIT_CARD", v["card"]),
        ]
        body = f"""<h1>Complete your order</h1><p class="muted">A synthetic checkout. Nothing is charged.</p><div class="grid"><section><h2>Shipping & payment</h2>{field("Full name", "name", "name")}{field("Shipping address", "address", "street-address")}{field("Card number", "card", "cc-number")}{field("Security code / CVV", "cvv", "cc-csc")}<button data-action="review">Review order</button><button data-action="purchase" hidden>Place demo order</button></section><section><span class="tag">ORDER SUMMARY</span><h2>Everyday carry backpack</h2><p>₹ 1,299 · Free delivery</p><h3>Saved customer</h3><p aria-label="Customer name">{e("name")}</p><p aria-label="Address">{e("address")}</p><p>Saved card: {e("card")}</p><p class="muted">Public order reference: ORD-2026-114</p></section></div>"""
    elif scenario == "authentication":
        truth = [("EMAIL_ADDRESS", v["email"]), ("PHONE_NUMBER", v["phone"])]
        body = f"""<h1>Welcome back</h1><div class="grid"><section><h2>Secure sign in</h2>{field("Email address", "email", "email")}{field("Password", "password", "current-password", "password")}{field("One-time code", "otp", "one-time-code")}<button class="secondary" data-action="reveal">Show password</button><button data-action="signin">Sign in</button></section><section><h2>Account recovery</h2><p>Recovery email: {e("email")}</p><p>Registered phone: {e("phone")}</p><p class="muted">Never share your password or verification code.</p></section></div>"""
    elif scenario == "support":
        truth = [("PHONE_NUMBER", v["phone"]), ("PRIVATE_MESSAGE", v["message"])]
        body = f"""<h1>Customer support desk</h1><div class="grid"><section aria-label="Private conversation"><h2>Private conversation</h2><p>Contact: {e("phone")}</p><p>{e("message")}</p></section><section><h2>Resolve request</h2><label for="category">Issue category</label><select id="category" aria-label="Issue category"><option>Choose category</option><option>Billing</option><option>Technical</option></select><label for="reply">Public reply</label><textarea id="reply" aria-label="Public reply"></textarea><button data-action="send">Send reply</button></section></div>"""
    elif scenario == "conference":
        truth = [
            ("PERSON", v["name"]),
            ("EMAIL_ADDRESS", v["email"]),
            ("PRIVATE_MESSAGE", v["message"]),
        ]
        body = f"""<h1>Design stand-up</h1><p class="muted">Synthetic meeting controls • observation-level protection</p><div class="grid"><section aria-label="Private participant information"><div class="row"><div><img class="tile" style="width:100%;object-fit:cover" src="/assets/fictional-participant.png" alt="AI-generated fictional participant"><p>{e("name")}</p></div><div><img class="tile" style="width:100%;object-fit:cover" src="/assets/fictional-participant.png" alt="AI-generated fictional participant"><p>{e("email")}</p></div></div></section><section aria-label="Private chat"><h2>Private chat</h2><p>{e("message")}</p></section></div><button data-action="mute">Mute microphone</button>"""
    else:
        truth = [
            ("API_KEY", v["api_key"]),
            ("IP_ADDRESS", v["ip"]),
            ("IN_PAN", v["pan"]),
        ]
        body = f"""<h1>Developer workspace</h1><div class="grid"><section><h2>API credentials</h2><p>Production-like synthetic key</p><code>{e("api_key")}</code><p>Allowed IP address: {e("ip")}</p><button data-action="details">Open key details</button><button data-action="revoke" hidden>Revoke demo key</button></section><section><h2>Billing identity</h2><p>PAN: {e("pan")}</p><p class="muted">Public build version: 1.4.2<br>Requests this month: 1200</p></section></div>"""
    script = """document.addEventListener('click',async e=>{const a=e.target.dataset.action;if(!a)return;if(a==='reveal'){const p=document.querySelector('#password');p.type=p.type==='password'?'text':'password';e.target.textContent=p.type==='text'?'Hide password':'Show password';return}if(a==='review'){document.querySelector('[data-action="purchase"]').hidden=false;return}if(a==='details'){document.querySelector('[data-action="revoke"]').hidden=false;return}const check=await fetch('/verify'+location.search,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:location.pathname.split('/').pop(),action:a,fields:Object.fromEntries(Array.from(document.querySelectorAll('input,textarea,select')).map(e=>[e.id,e.value]))})});if(!check.ok){document.querySelector('#result').hidden=false;document.querySelector('#result').textContent='Please complete the required fields correctly.';return}if(a==='mute')e.target.textContent='Unmute microphone';window.fixtureOutcome=a;document.querySelector('#result').hidden=false;document.querySelector('#result').textContent={'purchase':'Demo order placed','signin':'Signed in successfully','send':'Reply submitted','mute':'Microphone muted','revoke':'Demo key revoked'}[a]||'Action completed'});"""
    page = f'<!doctype html><html><head><meta charset="utf-8"><title>PrivacyLens synthetic {scenario}</title><style>{STYLE}</style></head><body class="{"variant" if layout else ""}"><header><strong>FIELDWORK / {scenario.upper()}</strong><span>SYNTHETIC SANDBOX</span></header><main>{body}<div id="result" role="status" hidden></div></main><script>{script}</script></body></html>'
    return page, truth, v
