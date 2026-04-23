@echo off
echo ========================================
echo Запуск Tax Project - Frontend + Backend
echo ========================================

echo.
echo [1/2] Запуск Backend (порт 8000)...
start "Tax Backend" cmd /k "cd /d C:\Users\kuzme\Tax\backend && C:\Users\kuzme\Tax\.venv\Scripts\python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo.
echo [2/2] Запуск Frontend...
start "Tax Frontend" cmd /k "cd /d C:\Users\kuzme\Tax\frontend && npm run dev"

echo.
echo ========================================
echo Готово! Открытые окна:
echo   - Backend: http://127.0.0.1:8000/docs
echo   - Frontend: http://localhost:5173
echo ========================================
echo.
echo Закрой окна, когда закончишь работу
pause
