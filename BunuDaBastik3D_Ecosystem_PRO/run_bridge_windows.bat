@echo off
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set BDB_BRIDGE_DB=%USERPROFILE%\.bunudabastik3d_ecosystem\controlcenter.sqlite3
if "%BDB_BRIDGE_PORT%"=="" set BDB_BRIDGE_PORT=8787
uvicorn cloud_bridge.main:app --host 0.0.0.0 --port %BDB_BRIDGE_PORT% --reload
pause
