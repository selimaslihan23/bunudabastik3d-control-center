@echo off
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
pyinstaller --noconfirm --onedir --console ^
 --name BunuDaBastik3D-ControlCenter-SAFE ^
 --icon assets\bdb_brand_icon.ico ^
 --paths app ^
 --hidden-import db ^
 --hidden-import pricing ^
 --hidden-import email_client ^
 --hidden-import makerworld ^
 --hidden-import odoo_client ^
 --hidden-import exporters ^
 --add-data "assets;assets" ^
 --add-data "app;app" ^
 app\main_safe.py

echo.
echo SAFE DEBUG EXE hazir:
echo dist\BunuDaBastik3D-ControlCenter-SAFE\BunuDaBastik3D-ControlCenter-SAFE.exe
echo.
pause
