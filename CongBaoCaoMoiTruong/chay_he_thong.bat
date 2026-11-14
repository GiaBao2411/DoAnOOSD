@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Cong bao cao su co moi truong - dang chay (dong cua so nay de tat web)
set PYTHONIOENCODING=utf-8

rem ---------- 1. Moi truong Python (.venv) va thu vien: lan dau tu cai ----------
if not exist ".venv\Scripts\python.exe" (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
  if errorlevel 1 (
    echo [LOI] Khong tim thay Python 3.10 tro len. Cai tai https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^).
    pause & exit /b 1
  )
  echo Lan dau: dang tao moi truong .venv va cai thu vien ^(can Internet, 1-3 phut^)...
  python -m venv .venv || ( echo [LOI] Khong tao duoc .venv & pause & exit /b 1 )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 ( echo [LOI] Cai thu vien that bai. Kiem tra Internet roi chay lai. & pause & exit /b 1 )
if not exist ".env" copy ".env.example" ".env" >nul

rem ---------- 2. Co so du lieu: tu tao database, 18 bang, du lieu mau neu chua co (dang nhap bang tai khoan Windows) ----------
".venv\Scripts\python.exe" -m app.seed
if errorlevel 1 ( pause & exit /b 1 )

rem ---------- 3. Jaeger (OpenTelemetry) bang Docker: chi bat khi Docker Desktop dang chay ----------
set OTEL_EXPORTER_OTLP_ENDPOINT=
docker info >nul 2>nul
if errorlevel 1 (
  echo [CHU Y] Docker Desktop chua chay: web van chay, nhung khong bat Jaeger/OpenTelemetry.
) else (
  docker compose up -d >nul 2>nul && set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
)

rem ---------- 4. Chay web (FastAPI + giao dien React da build) ----------
echo ============================================================
echo  Web:     http://localhost:8000
if defined OTEL_EXPORTER_OTLP_ENDPOINT echo  Jaeger:  http://localhost:16686   ^(xem trace OpenTelemetry^)
echo  Pico W / dien thoai cung WiFi dung IP cua laptop:
ipconfig | findstr /i "IPv4"
echo  SERVER_URL trong main.py = "http://IP_LAPTOP:8000/api/tram/so-lieu"
echo  Dong cua so nay ^(hoac Ctrl+C^) de tat web. Tat Jaeger: tat_he_thong.bat
echo ============================================================
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8000"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
