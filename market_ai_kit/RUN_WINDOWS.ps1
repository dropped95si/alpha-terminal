$ErrorActionPreference = "Stop"

Write-Host "[1/4] Creating venv (if missing)..."
if (!(Test-Path "venv")) { python -m venv venv }

Write-Host "[2/4] Activating venv..."
.\venv\Scripts\Activate.ps1

Write-Host "[3/4] Installing requirements..."
# (disabled) pip install --upgrade pip
pip install -r requirements.txt

Write-Host "[4/4] Running scan..."
if (!(Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }

python -m scanner.run --config config.yaml

Write-Host "Done. Check the output folder for JSON results."

Write-Host "Tip: Open output\report.html in your browser." -ForegroundColor Yellow
