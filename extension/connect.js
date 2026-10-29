(async () => {
  try {
    const {token} = await (await fetch('/api/bootstrap')).json();
    const response = await fetch('/api/extension/pair-code', {headers:{'x-privacy-session':token}});
    if (!response.ok) throw new Error('Connection code unavailable');
    const {code} = await response.json();
    document.getElementById('code').textContent = code;
    document.getElementById('copy').onclick = async () => {await navigator.clipboard.writeText(code);document.getElementById('message').textContent='Copied. Paste into the PrivacyLens side panel.'};
  } catch {document.getElementById('message').textContent='Start the local PrivacyLens server, then reload this page.'}
})();
