# Windows uchun bir martalik o'rnatish: Python tekshiruvi -> venv -> paketlar -> demo ma'lumot -> testlar
# Ishga tushirish (loyiha ildizidan):  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 1) Mos Python topish (3.11 - 3.14). `py` launcher bo'lsa aniq versiyani tanlaymiz.
$pyExe = $null
$pyArgs = @()
foreach ($v in @("3.12", "3.13", "3.11", "3.14")) {
    try {
        $null = & py "-$v" -c "import sys" 2>&1
        if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-$v"); break }
    } catch { }
}
if (-not $pyExe) {
    try { $ver = (& python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>&1) } catch { $ver = $null }
    if (-not $ver -or $LASTEXITCODE -ne 0) {
        throw "Python topilmadi. https://www.python.org/downloads/ dan 3.12 ni o'rnating ('Add python.exe to PATH' belgilang)."
    }
    if ([version]$ver -lt [version]"3.11") { throw "Python $ver juda eski. 3.11 yoki undan yangi versiya kerak (tavsiya: 3.12)." }
    $pyExe = "python"
}
Write-Host "Python: $pyExe $($pyArgs -join ' ')" -ForegroundColor Cyan

# 2) Virtual muhit
if (-not (Test-Path ".venv")) { & $pyExe @pyArgs -m venv .venv }
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r backend\requirements.txt

# 3) .env va demo ma'lumot
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
& $venvPython scripts\seed.py --reset

# 4) Testlar
Push-Location backend
try { & $venvPython -m pytest -q } finally { Pop-Location }

Write-Host ""
Write-Host "Tayyor. Ishga tushirish:" -ForegroundColor Green
Write-Host "  .venv\Scripts\activate"
Write-Host "  cd backend; uvicorn app.main:app --reload      # http://localhost:8000/docs"
Write-Host "  streamlit run frontend\streamlit_app.py       # http://localhost:8501"
Write-Host "Yoki bittada:  powershell -ExecutionPolicy Bypass -File scripts\run_dev.ps1"
