# Start backend (uvicorn) in background and then run Streamlit frontend
$ErrorActionPreference = 'Stop'

Write-Output "Starting backend (uvicorn) in background..."
Start-Process -NoNewWindow -FilePath pwsh -ArgumentList "-NoLogo -NoProfile -Command \"python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\""
Start-Sleep -Seconds 2

Write-Output "Starting Streamlit frontend..."
python -m streamlit run frontend/streamlit_app.py --server.port 8501
