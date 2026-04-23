@echo off
cd /d C:\Users\kuzme\Tax\backend
set PYTHONPATH=C:\Users\kuzme\Tax\backend
C:\Users\kuzme\Tax\.venv\Scripts\python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000 --reload
pause
