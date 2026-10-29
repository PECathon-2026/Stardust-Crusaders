$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $PSScriptRoot '.tools/browsers'
$env:TEMP = Join-Path $PSScriptRoot '.runtime/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
if (!(Test-Path '.venv/Scripts/python.exe')) { throw 'Run setup.ps1 first.' }
& '.venv/Scripts/python.exe' -c "from playwright.sync_api import sync_playwright; from pathlib import Path; p=sync_playwright().start(); exists=Path(p.chromium.executable_path).exists(); p.stop(); raise SystemExit(0 if exists else 1)"
if ($LASTEXITCODE -ne 0) {
    & '.venv/Scripts/python.exe' -m playwright install chromium --no-shell
    if ($LASTEXITCODE -ne 0) { throw 'Browser installation failed.' }
}
Write-Host 'Opening a browser with PrivacyLens installed. Keep the local server running.'
& '.venv/Scripts/python.exe' extension_browser.py
