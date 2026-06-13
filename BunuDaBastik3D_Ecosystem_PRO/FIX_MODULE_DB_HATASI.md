# ModuleNotFoundError: No module named db düzeltmesi

Bu paket PyInstaller build komutuna şu düzeltmeleri ekler:

- `--paths app`
- `--hidden-import db` ve diğer yerel modüller
- `--add-data "app;app"`
- Paketli EXE içinde `sys._MEIPASS/app` yolundan yerel modülleri yükleme

## Önerilen kullanım

1. Klasörü `C:\BDB\` gibi Türkçe/özel karakter içermeyen bir dizine çıkar.
2. `build_windows.bat` çalıştır.
3. Sadece `dist\BunuDaBastik3D-ControlCenter-PRO.exe` dosyasını aç.

Tek dosya EXE sorun çıkarırsa:

1. `build_windows_ONEDIR_SAFE.bat` çalıştır.
2. `dist\BunuDaBastik3D-ControlCenter-PRO\BunuDaBastik3D-ControlCenter-PRO.exe` dosyasını aç.
3. `_internal` klasörünü silme veya EXE'den ayırma.
