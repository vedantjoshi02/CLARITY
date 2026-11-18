$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# Use regular 64-bit CPython 3.14.2 or a later 3.14 patch release.
$checkPython = "import sys, struct, sysconfig; sys.exit(0 if (3,14,2) <= sys.version_info[:3] < (3,15,0) and struct.calcsize('P') == 8 and not sysconfig.get_config_var('Py_GIL_DISABLED') else 1)"
py -3.14 -c $checkPython
if ($LASTEXITCODE -ne 0) { throw 'Install standard 64-bit Python 3.14.2 (or a newer 3.14 patch), including the Python launcher, then retry.' }

# Virtual environments cannot be upgraded by copying a new interpreter into them.
# Keep the old environment as a backup; database, uploads and .env stay untouched.
if (Test-Path '.venv') {
    $compatible = $false
    if (Test-Path '.venv\Scripts\python.exe') {
        & .\.venv\Scripts\python.exe -c $checkPython
        $compatible = ($LASTEXITCODE -eq 0)
    }
    if (-not $compatible) {
        $backupName = '.venv-backup-' + [Guid]::NewGuid().ToString('N')
        Move-Item -Path '.venv' -Destination $backupName
        Write-Host "Previous environment preserved as $backupName"
    }
}
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3.14 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python 3.14 environment.' }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip.' }
& .\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Use standard 64-bit CPython 3.14 and check your internet connection.' }
if (-not (Test-Path '.env')) {
    Copy-Item .env.example .env
    $secret = & .\.venv\Scripts\python.exe -c 'import secrets; print(secrets.token_urlsafe(48))'
    if ($LASTEXITCODE -ne 0) { throw 'Secret generation failed.' }
    (Get-Content .env -Raw).Replace('replace-with-a-long-random-secret', $secret.Trim()) | Set-Content .env
}
& .\.venv\Scripts\python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
& .\.venv\Scripts\python.exe manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Academic setup failed.' }
& .\.venv\Scripts\python.exe manage.py shell -c 'import sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 2)'
if ($LASTEXITCODE -eq 2) {
    Write-Host 'Create your administrator account. No default password is shipped.'
    & .\.venv\Scripts\python.exe manage.py createsuperuser
    if ($LASTEXITCODE -ne 0) { throw 'Administrator creation was not completed.' }
} elseif ($LASTEXITCODE -ne 0) { throw 'Could not check the existing administrator account.' }
& .\.venv\Scripts\python.exe manage.py seed_demo --resources
if ($LASTEXITCODE -ne 0) { throw 'Sample resource setup failed.' }
& .\.venv\Scripts\python.exe manage.py check
if ($LASTEXITCODE -ne 0) { throw 'Django system checks failed.' }
Write-Host 'Ready! Run .\run.ps1 and open http://127.0.0.1:8000'
