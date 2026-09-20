$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "尚未安装，请先运行 install_local.ps1"
    exit 1
}

$port = if ($env:CASEFLOW_PORT) { $env:CASEFLOW_PORT } else { "8080" }
$url = "http://127.0.0.1:$port"
Start-Process $url
& .\.venv\Scripts\python.exe -m waitress --listen="127.0.0.1:$port" app:app
