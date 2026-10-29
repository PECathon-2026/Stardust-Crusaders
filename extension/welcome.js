let windowId;
chrome.windows.getCurrent().then(w=>{windowId=w.id});
document.getElementById('open').addEventListener('click',()=>{
  chrome.sidePanel.open({windowId}).catch(()=>{document.getElementById('message').textContent='Use the PrivacyLens toolbar icon to open the panel.'});
});
