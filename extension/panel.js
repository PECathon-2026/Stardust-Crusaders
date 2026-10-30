const BASE = 'http://127.0.0.1:8765';
const $ = id => document.getElementById(id);
let token = '', socket = null, ready = false, boundTab = null, boundOrigin = '', controlling = false;
let state = {}, inspection = null, original = false, guard = null, polling = false, pausing = false, operation = false, activeRunId = null;
const examples = {
  checkout:'Fill the checkout form using the permitted local secret references, review the order and request approval before placing the demo order.',
  authentication:'Fill the email, password and one-time code using local secret references, then sign in.',
  support:'Set the issue category to "Billing". Enter the public reply "I can help with your billing question." and request approval to send it.',
  conference:'Mute the microphone without exposing participant identities or private chat.',
  developer:'Open the key details and request approval before revoking the demo key.',
  saucedemo:'Log in using the permitted demonstration credentials if needed, add the Sauce Labs Backpack to the cart, open the cart and stop before checkout.'
};
function scenario(url) {
  try {
    const u = new URL(url);
    if (u.username || u.password || u.hash) return null;
    if (u.origin==='http://127.0.0.1:8766' && /^\/scenario\/(checkout|authentication|support|conference|developer)$/.test(u.pathname) && [...u.searchParams.keys()].every(k=>['seed','layout'].includes(k))) return u.pathname.split('/').pop();
    if (u.origin==='https://www.saucedemo.com' && ['/', '/index.html','/inventory.html','/cart.html'].includes(u.pathname) && !u.search) return 'saucedemo';
  } catch {}
  return null;
}
function error(message='') {$('error').textContent=message}
async function api(path, body) {
  const response = await fetch(BASE+'/api/'+path, {method:body===undefined?'GET':'POST', headers:{'content-type':'application/json','x-privacy-session':token}, ...(body===undefined?{}:{body:JSON.stringify(body)})});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Local request rejected');
  return data;
}
async function action(fn) {error();try {await fn()} catch(e) {error(e.message || 'Operation stopped safely')}}
async function currentTab() {return (await chrome.tabs.query({active:true,currentWindow:true}))[0]}
async function updateTab() {
  const tab = await currentTab();
  $('tab-name').textContent = tab?.title || 'No active tab';
  $('tab-url').textContent = tab?.url || '';
  $('start').disabled = !ready || controlling || !scenario(tab?.url) || !['completed','blocked','stopped','paused','needs_review',undefined].includes(state.run?.status);
}
async function command(method, params={}) {
  if (boundTab===null || !controlling) throw new Error('Manual control');
  const tab = await chrome.tabs.get(boundTab);
  if (!scenario(tab.url) || new URL(tab.url).origin!==boundOrigin) throw new Error('Tab origin changed');
  return await chrome.debugger.sendCommand({tabId:boundTab}, method, params);
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:false});
  if (result.exceptionDetails) throw new Error('Page evaluation rejected');
  return result.result?.value;
}
async function checkGuard() {
  if (!guard) throw new Error('Missing observation guard');
  const current = await evaluate(guard.expression);
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(current)))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if (hash!==guard.fingerprint) throw new Error('Stale observation');
}
async function rpc(message) {
  const p=message.params || {};
  if (!controlling) throw new Error('Manual control');
  if (message.method==='evaluate') return {value:await evaluate(p.expression),url:(await chrome.tabs.get(boundTab)).url};
  if (message.method==='screenshot') {
    const size=await evaluate('({width:innerWidth,height:innerHeight})');
    const image=await command('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
    return {...size,data:image.data,url:(await chrome.tabs.get(boundTab)).url};
  }
  if (message.method==='guard') {guard=p;return true}
  if (message.method!=='action') throw new Error('Unsupported browser command');
  await checkGuard();
  if (p.action==='scroll') {
    if (![500,-500].includes(p.delta)) throw new Error('Invalid scroll');
    await evaluate(`window.scrollBy(0,${p.delta})`);return true;
  }
  if (!/^\[data-pl-target="e_[a-f0-9]{32}"\]$/.test(p.selector)) throw new Error('Invalid target');
  const selector=JSON.stringify(p.selector);
  const point=await evaluate(`(()=>{const es=document.querySelectorAll(${selector});if(es.length!==1||es[0].disabled)throw Error('target');const e=es[0],r=e.getBoundingClientRect();if(r.width<=0||r.height<=0||getComputedStyle(e).visibility==='hidden')throw Error('hidden');return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  if (p.action==='click') {
    await command('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});
    await command('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1});
  } else if (p.action==='fill') {
    if (typeof p.value!=='string'||p.value.length>2000) throw new Error('Invalid fill');
    await evaluate(`(()=>{const e=document.querySelector(${selector});if(!['INPUT','TEXTAREA'].includes(e.tagName)||['file','submit','button','checkbox','radio'].includes(e.type))throw Error('field');e.focus();const proto=e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(e,${JSON.stringify(p.value)});e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`);
  } else if (p.action==='select') {
    await evaluate(`(()=>{const e=document.querySelector(${selector});if(e.tagName!=='SELECT')throw Error('select');const o=[...e.options].find(o=>o.label===${JSON.stringify(p.value)}&&!o.disabled);if(!o)throw Error('option');e.value=o.value;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`);
  } else throw new Error('Unsupported action');
  guard=null;return true;
}
async function connect() {
  if (socket) socket.close();
  ready=false;
  socket=new WebSocket('ws://127.0.0.1:8765/api/extension/ws');
  socket.onopen=()=>socket.send(JSON.stringify({token}));
  socket.onmessage=async event=>{
    const message=JSON.parse(event.data);
    if (message.type==='ready') {ready=true;$('pairing').hidden=true;$('workspace').hidden=false;$('connection').textContent='Local engine connected';await refresh();return}
    if (message.type!=='rpc') return;
    try {const result=await rpc(message);if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify({type:'rpc_result',id:message.id,ok:true,result}))}
    catch {if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify({type:'rpc_result',id:message.id,ok:false}))}
  };
  socket.onclose=()=>{ready=false;controlling=false;guard=null;$('connection').textContent='Disconnected';$('status').textContent='Local connection closed. Your tab remains open.';void detach();$('pairing').hidden=false;};
  socket.onerror=()=>error('Cannot connect. Start the local server and reconnect using its current code.');
}
async function detach() {if(boundTab!==null){const old=boundTab;boundTab=null;try{await chrome.debugger.detach({tabId:old})}catch{}}}
async function attach() {
  const tab=await currentTab();
  if(!scenario(tab?.url))throw new Error('Open a listed demo page or SauceDemo first.');
  if(boundTab!==tab.id){await detach();await chrome.debugger.attach({tabId:tab.id},'1.3');boundTab=tab.id;}
  boundOrigin=new URL(tab.url).origin;guard=null;controlling=true;
  return tab;
}
async function takeControl() {
  if(pausing)return;pausing=true;controlling=false;guard=null;
  try {await api('extension/pause',{});await detach();$('status').textContent='You have control. Interact with the website, then click Run on this tab to resume with a fresh observation.';}finally{pausing=false;await refresh()}
}
function drawPreview() {
  const preview=inspection || state.run?.preview;
  $('preview').hidden=!preview;
  if(preview){$('preview').src=original?preview.original:preview.sanitized;$('findings').textContent=(preview.findings||[]).map(f=>f.kind+' — '+f.reason).slice(0,12).join(' · ')}
  else {$('preview').removeAttribute('src');$('findings').textContent='Inspect the current page or start a task to view local protection.'}
  $('preview-toggle').textContent=original?'Show sanitized view':'Show local original';
}
async function refresh() {
  if(!ready||polling)return;polling=true;
  try {
    state=await api('status');const r=state.run;
    for(const name of Object.keys(examples))if(state.scenarios?.[name])examples[name]=state.scenarios[name];
    $('status').textContent=state.initializing?'Preparing local detectors…':r?.status==='paused'?'You have control. Run again to continue from the current page.':state.provider_status?.state==='pacing'&&controlling?'Waiting for the local request budget. Take control remains available.':r?.status==='completed'?'Verified page outcome: '+r.outcome:r?.status==='needs_review'?'Planner finished; inspect the website to confirm the result.':r?.status||'Ready';
    if(r?.error)error(r.error);
    $('approval').hidden=!r?.approval;
    if(r?.approval)$('approval-title').textContent=r.approval.title;
    $('events').replaceChildren(...(r?.events||[]).slice(-6).map(e=>{const li=document.createElement('li');li.textContent=e.title;const small=document.createElement('small');small.textContent=e.detail;li.append(small);return li}));
    $('receipts').replaceChildren(...(r?.receipts||[]).slice(-5).map(r=>{const div=document.createElement('div');div.className='receipt';div.textContent=`${r.destination||r.decision} · ${r.bytes||0} bytes · ${r.image_disclosed?'sanitized image approved':'no image disclosure'} · ${r.digest||'blocked before transport'}`;return div}));
    $('pause').disabled=!controlling;
    for(const id of ['provider','privacy-profile','demo-secrets','draft-only','prompt'])$(id).disabled=controlling;
    if(controlling&&!operation&&r?.id===activeRunId&&['completed','blocked','needs_review','stopped'].includes(r.status)){controlling=false;await detach()}
    drawPreview();await updateTab();
  } catch(e){error(e.message)}finally{polling=false}
}
$('get-code').onclick=()=>chrome.tabs.create({url:BASE+'/extension-connect'});
$('pair').onclick=()=>action(async()=>{const result=await api('extension/pair',{code:$('pair-code').value.trim()});token=result.token;$('pair-code').value='';await chrome.storage.session.set({privacyToken:token});await connect()});
$('open-demo').onclick=()=>action(async()=>{if(controlling)await takeControl();const name=$('demo-page').value;await chrome.tabs.create({url:name==='saucedemo'?'https://www.saucedemo.com/':'http://127.0.0.1:8766/scenario/'+name});$('prompt').value=examples[name];$('demo-secrets').checked=true;$('privacy-profile').value='private';await updateTab()});
$('example').onclick=()=>action(async()=>{const name=scenario((await currentTab())?.url);if(!name)throw new Error('Open a supported page first');$('prompt').value=examples[name]});
$('start').onclick=()=>action(async()=>{
  if($('prompt').value.trim().length<3)throw new Error('Enter your task first');
  operation=true;inspection=null;
  try {const tab=await attach();const result=await api('extension/run',{url:tab.url,task:$('prompt').value,provider:$('provider').value,demo_secrets:$('demo-secrets').checked,privacy_profile:$('privacy-profile').value,draft_only:$('draft-only').checked});activeRunId=result.id;await refresh()}catch(e){controlling=false;await detach();throw e}finally{operation=false}
});
$('pause').onclick=()=>action(takeControl);
$('stop').onclick=()=>action(async()=>{controlling=false;guard=null;await api('stop',{});await detach();inspection=null;await refresh()});
for(const [id,approved]of [['approve',true],['decline',false]])$(id).onclick=()=>action(async()=>{await api('approve',{approval_id:state.run.approval.id,approved});await refresh()});
$('save-keys').onclick=()=>action(async()=>{await api('settings',{api_key:$('gemini-key').value,groq_api_key:$('groq-key').value,gemini_model:$('gemini-model').value,groq_model:state.groq_model||'openai/gpt-oss-120b',headless:state.headless??true});$('gemini-key').value='';$('groq-key').value='';$('status').textContent='Provider settings saved locally.'});
$('save-secret').onclick=()=>action(async()=>{await api('secrets',{reference:$('secret-ref').value,value:$('secret-value').value});$('secret-value').value='';$('status').textContent='Secret stored in local memory.'});
$('inspect').onclick=()=>action(async()=>{if(controlling)throw new Error('Take control before inspecting manually');operation=true;try{const tab=await attach();inspection=(await api('extension/inspect',{url:tab.url,task:'Inspect privately',provider:'demo',demo_secrets:$('demo-secrets').checked,privacy_profile:$('privacy-profile').value})).preview;drawPreview()}finally{operation=false;controlling=false;await detach()}});
$('preview-toggle').onclick=()=>{original=!original;drawPreview()};
$('open-lab').onclick=()=>chrome.tabs.create({url:BASE+'/lab'});
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>{for(const name of ['task','privacy','settings'])$('view-'+name).hidden=name!==button.dataset.view;};
chrome.tabs.onActivated.addListener(()=>{if(controlling)void action(takeControl);void updateTab()});
chrome.tabs.onUpdated.addListener((id,change)=>{if(id===boundTab&&change.url&&new URL(change.url).origin!==boundOrigin&&controlling)void action(takeControl);void updateTab()});
chrome.debugger.onDetach.addListener((source)=>{if(source.tabId===boundTab){boundTab=null;if(controlling)void action(takeControl)}});
window.addEventListener('pagehide',()=>{controlling=false;if(socket)socket.close();void detach()});
setInterval(()=>{void refresh()},1200);
chrome.storage.session.get('privacyToken').then(async data=>{if(data.privacyToken){token=data.privacyToken;await connect()}});
void updateTab();
