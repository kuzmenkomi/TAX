# Запуск frontend и backend для проверки работы сайта

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Запуск Tax Project" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Проверка frontend
Write-Host "`n[1/2] Проверка frontend..." -ForegroundColor Yellow
$frontendPath = "C:\Users\kuzme\Tax\frontend"
if (Test-Path "$frontendPath\node_modules") {
    Write-Host "✓ node_modules найдены" -ForegroundColor Green
} else {
    Write-Host "✗ node_modules НЕ найдены, установка..." -ForegroundColor Red
    Set-Location $frontendPath
    npm install
}

# Запуск frontend в фоне
Write-Host "✓ Запуск frontend на http://localhost:5173" -ForegroundColor Green
Set-Location $frontendPath
Start-Process -FilePath "node" -ArgumentList "run", "dev" -NoNewWindow

Start-Sleep -Seconds 3

# Проверка backend
Write-Host "`n[2/2] Проверка backend..." -ForegroundColor Yellow
$backendPath = "C:\Users\kuzme\Tax\backend"
$venvPython = "C:\Users\kuzme\Tax\.venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "✓ Python virtualenv найден" -ForegroundColor Green
} else {
    Write-Host "✗ Python virtualenv НЕ найден!" -ForegroundColor Red
    exit 1
}

# Запуск backend в фоне
Write-Host "✓ Запуск backend на http://127.0.0.1:8000" -ForegroundColor Green
Set-Location $backendPath
Start-Process -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.api.server:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -NoNewWindow

Start-Sleep -Seconds 5

# Проверка портов
Write-Host "`nПроверка портов..." -ForegroundColor Yellow
$backendRunning = (netstat -ano | Select-String "8000") -ne $null
$frontendRunning = (netstat -ano | Select-String "5173") -ne $null

if ($backendRunning) {
    Write-Host "✓ Backend запущен на порту 8000" -ForegroundColor Green
} else {
    Write-Host "✗ Backend НЕ запущен!" -ForegroundColor Red
}

if ($frontendRunning) {
    Write-Host "✓ Frontend запущен на порту 5173" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend НЕ запущен!" -ForegroundColor Red
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Готово! Открой в браузере:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`nНажми любую клавишу для остановки сервисов..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Остановка процессов
Write-Host "Остановка сервисов..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force

Write-Host "Сервисы остановлены." -ForegroundColor Green
