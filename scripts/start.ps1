param()

$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

$venvDir = Join-Path $PWD '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$requirements = Join-Path $PWD 'requirements.txt'
$envExample = Join-Path $PWD '.env.example'
$envFile = Join-Path $PWD '.env'

if (-not (Test-Path $venvPython)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    }

    if (-not $pythonCommand) {
        throw 'Python is not available in PATH. Install Python 3.10+ first.'
    }

    if (Test-Path $venvDir) {
        Remove-Item -Recurse -Force $venvDir
    }

    & $pythonCommand.Source -m venv $venvDir
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirements

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host '.env created from .env.example'
}

& $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload