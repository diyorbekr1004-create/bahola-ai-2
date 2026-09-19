# Backend (uvicorn) ni fon rejimida, Streamlit frontendni oldingi planda ishga tushiradi (Windows PowerShell)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (Test-Path ".env") {
    Get-Content .env | Where-Object { $_ -match '^\s*[^#][^=]*=' } | ForEach-Object {
        $k, $v = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim())
    }
}
if (-not $env:BACKEND_URL) { $env:BACKEND_URL = "http://localhost:8000" }

Write-Output "Backend: http://localhost:8000/docs"
$backend = Start-Process -PassThru -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory (Join-Path $root "backend")
Start-Sleep -Seconds 2
try {
    Write-Output "Frontend: http://localhost:8501"
    python -m streamlit run frontend/streamlit_app.py --server.port 8501
} finally {
    if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id }
}
