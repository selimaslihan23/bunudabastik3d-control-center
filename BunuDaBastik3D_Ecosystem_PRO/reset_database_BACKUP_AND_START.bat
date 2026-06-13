@echo off
chcp 65001 >nul
set APPDB=%USERPROFILE%\.bunudabastik3d_ecosystem\controlcenter.sqlite3
set BACKUPDIR=%USERPROFILE%\.bunudabastik3d_ecosystem\manual_backups
if not exist "%BACKUPDIR%" mkdir "%BACKUPDIR%"
if exist "%APPDB%" (
  copy "%APPDB%" "%BACKUPDIR%\controlcenter_before_reset.sqlite3" >nul
  del "%APPDB%"
  echo Eski veritabani yedeklendi ve sifirlandi.
) else (
  echo Eski veritabani bulunamadi, yeni temiz veritabani olusturulacak.
)
call run_windows_REPAIR_CRUD.bat
