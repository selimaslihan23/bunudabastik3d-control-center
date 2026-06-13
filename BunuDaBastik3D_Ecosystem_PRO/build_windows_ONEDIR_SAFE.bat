@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo BunuDaBastik3D Control Center - ONEDIR Build
echo ============================================================
echo Bu mod EXE + _internal klasoru olusturur.
echo EXE tek basina kopyalanmaz. Tum dist klasoru birlikte kullanilir.
echo.
py -c "import os, sys; p=os.getcwd(); print('Klasor:', p); print('ASCII yol:', p.isascii()); sys.exit(0 if p.isascii() else 1)"
if errorlevel 1 (
  echo.
  echo UYARI: Klasor yolunda Turkce/ozel karakter var.
  echo C:\BDB gibi duz bir klasore tasiyip tekrar build alin.
  echo.
  pause
)

if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller --clean --noconfirm --onedir --windowed --name BunuDaBastik3D-ControlCenter-PRO --icon assets\bdb_brand_icon.ico --paths "app" --hidden-import db --hidden-import email_client --hidden-import makerworld --hidden-import pricing --hidden-import odoo_client --hidden-import exporters --add-data "assets;assets" --add-data "app;app" app\main.py

echo.
echo EXE burada:
echo dist\BunuDaBastik3D-ControlCenter-PRO\BunuDaBastik3D-ControlCenter-PRO.exe
echo.
echo ONEMLI: Bu exe'nin yanindaki _internal klasoru silinmez/tasinmaz.
echo build klasorundeki exe kullanilmaz.
pause
