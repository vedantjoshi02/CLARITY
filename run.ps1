$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run setup.ps1 first.' }
& .\.venv\Scripts\python.exe -c 'import sys; sys.exit(0 if (3,14,2) <= sys.version_info[:3] < (3,15,0) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'This environment is not Python 3.14.2+. Run setup.ps1 to prepare a compatible environment.' }
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
