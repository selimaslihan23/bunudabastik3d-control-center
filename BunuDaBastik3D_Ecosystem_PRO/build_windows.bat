@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo BunuDaBastik3D Control Center - Temiz EXE Build
echo ============================================================
echo.
py -c "import os, sys; p=os.getcwd(); print('Klasor:', p); print('ASCII yol:', p.isascii()); sys.exit(0 if p.isascii() else 1)"
if errorlevel 1 (
  echo.
  echo UYARI: Klasor yolunda Turkce/ozel karakter var.
  echo Ornek: C:\Users\SELIM yerine C:\BDB gibi duz bir klasore tasiyip tekrar deneyin.
  echo Bu durum PyInstaller python DLL yukleme hatasina yol acabilir.
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

pyinstaller --clean --noconfirm --onefile --windowed --name BunuDaBastik3D-ControlCenter-PRO --icon assets\bdb_brand_icon.ico --paths "app" --hidden-import db --hidden-import email_client --hidden-import makerworld --hidden-import pricing --hidden-import odoo_client --hidden-import exporters --add-data "assets;assets" --add-data "app;app" app\main.py

echo.
echo ============================================================
echo EXE hazir:
echo dist\BunuDaBastik3D-ControlCenter-PRO.exe
echo.
echo NOT: build klasorundeki dosyalari calistirmayin.
echo Sadece dist klasorundeki EXE'yi kullanin.
echo ============================================================
pause
