@echo off
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set BDB_BRIDGE_DB=%USERPROFILE%\.bunudabastik3d_ecosystem\controlcenter.sqlite3
uvicorn cloud_bridge.main:app --host 0.0.0.0 --port 8787 --reload
pause
