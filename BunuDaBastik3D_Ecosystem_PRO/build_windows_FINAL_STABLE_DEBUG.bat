@echo off
chcp 65001 >nul
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
pyinstaller --clean --noconfirm --onedir --console ^
 --name BunuDaBastik3D-ControlCenter-FINAL-STABLE-DEBUG ^
 --icon assets\bdb_brand_icon.ico ^
 --paths app ^
 --hidden-import db ^
 --hidden-import pricing ^
 --hidden-import email_client ^
 --hidden-import google_oauth_client ^
 --hidden-import makerworld ^
 --hidden-import odoo_client ^
 --hidden-import exporters ^
 --collect-all googleapiclient ^
 --collect-all google_auth_oauthlib ^
 --collect-all google.oauth2 ^
 --collect-all google.auth ^
 --add-data "assets;assets" ^
 --add-data "app;app" ^
 app\main_safe.py
pause
