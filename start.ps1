$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe') -or !(Test-Path 'frontend/dist/index.html')) {
    throw 'Run setup.ps1 first.'
}
Write-Host 'PrivacyLens: http://127.0.0.1:8765 — keep this terminal open. Ctrl+C stops the server.'
& '.venv/Scripts/python.exe' -m backend.serve
