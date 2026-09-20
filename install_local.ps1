$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
& .\.venv\Scripts\python.exe -c "from app import init_db; init_db()"

Write-Host "CaseFlow 安装完成。运行 powershell -ExecutionPolicy Bypass -File start_local.ps1 启动。"
