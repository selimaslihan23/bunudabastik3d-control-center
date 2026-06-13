@echo off
cd /d %~dp0
if not exist logs mkdir logs
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set BDB_SAFE_MODE=1
set BDB_DEBUG=1
python app\main.py --safe --debug > logs\run_safe_console.log 2>&1
if errorlevel 1 (
  echo.
  echo Uygulama hata verdi. Log dosyalari:
  echo - logs\run_safe_console.log
  echo - %%LOCALAPPDATA%%\BunuDaBastik3D\logs\app_debug.log
  pause
)
