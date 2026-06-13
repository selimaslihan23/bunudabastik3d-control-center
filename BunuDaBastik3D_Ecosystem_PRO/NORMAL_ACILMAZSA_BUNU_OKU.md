# Normal sürüm arka planda çalışıp pencere açmıyorsa

Bu durum genelde splash/login penceresinin Windows/PyInstaller ortamında görünememesi ya da pencere odağının takılmasıdır.

## Hızlı çözüm

1. Görev Yöneticisi'nden çalışan eski BunuDaBastik3D işlemlerini sonlandır.
2. `run_windows_SAFE.bat` dosyasını çalıştır.
3. Bu sürüm splash/login ekranını atlar ve ana pencereyi direkt açar.

## EXE olarak güvenli sürüm üretmek

`build_windows_SAFE_DEBUG.bat` çalıştır.

Sonra şu dosyayı aç:

`dist\BunuDaBastik3D-ControlCenter-SAFE\BunuDaBastik3D-ControlCenter-SAFE.exe`

## Log dosyaları

Hata varsa şu dosyalara bak:

- `logs\run_safe_console.log`
- `%LOCALAPPDATA%\BunuDaBastik3D\logs\app_debug.log`

Bu dosyaları ChatGPT'ye gönderirsen hata nokta atışı düzeltilebilir.
