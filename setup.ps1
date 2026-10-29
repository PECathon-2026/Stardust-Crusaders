$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Setup command failed ($LASTEXITCODE)." } }
python -m pip install --user uv
Check-Exit
python -m uv python install 3.11.9
Check-Exit
if (!(Test-Path '.venv/Scripts/python.exe')) { python -m uv venv --python 3.11.9 .venv; Check-Exit }
$dependencyList = if (Test-Path 'requirements.lock.txt') { 'requirements.lock.txt' } else { 'requirements.txt' }
python -m uv pip install --python .venv/Scripts/python.exe -r $dependencyList
Check-Exit
python -m uv pip install --python .venv/Scripts/python.exe 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'
Check-Exit
if (!(Test-Path 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')) {
    & '.venv/Scripts/python.exe' -m playwright install chromium
    Check-Exit
}
& '.venv/Scripts/python.exe' -m playwright install ffmpeg
Check-Exit
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest 'https://media.githubusercontent.com/media/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/face_detection_yunet_2023mar.onnx' -OutFile 'models/yunet.onnx'
if ((Get-FileHash 'models/yunet.onnx').Hash -ne '8F2383E4DD3CFBB4553EA8718107FC0423210DC964F9F4280604804ED2552FA4') { throw 'YuNet model checksum mismatch' }
& '.venv/Scripts/python.exe' -c "from backend.privacy import Detector; d=Detector(); print(d.initialize()); assert all(d.status.values()), 'A local detector failed to initialize'"
Check-Exit
Push-Location frontend
try { npm.cmd ci; Check-Exit; npm.cmd run build; Check-Exit } finally { Pop-Location }
Write-Host 'Setup complete. Run .\start.ps1'
