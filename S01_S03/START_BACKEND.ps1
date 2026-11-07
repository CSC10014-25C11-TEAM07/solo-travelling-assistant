Set-Location (Join-Path $PSScriptRoot "backend")
py -m pip install -r requirements.txt
py -m uvicorn main:app --host 0.0.0.0 --port 8000
