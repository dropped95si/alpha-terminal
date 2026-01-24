Write-Host "[SELFTEST] Activating venv..." -ForegroundColor Cyan
. .\venv\Scripts\Activate.ps1

Write-Host "[SELFTEST] Python version:" -ForegroundColor Cyan
python -c "import sys; print(sys.version)"

Write-Host "[SELFTEST] Compileall (syntax check)..." -ForegroundColor Cyan
python -m compileall -q .

Write-Host "[SELFTEST] Running unit tests (offline)..." -ForegroundColor Cyan
python -m unittest -v

Write-Host "[SELFTEST] Done." -ForegroundColor Green
