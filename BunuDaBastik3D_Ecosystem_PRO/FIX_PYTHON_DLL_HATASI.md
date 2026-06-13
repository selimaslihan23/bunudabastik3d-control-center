# Python DLL Hatası Çözümü

Görülen hata:

`Failed to load Python DLL ... _internal\python314.dll`

Bu hata genelde uygulama kodundan değil, EXE paketleme/çalıştırma konumundan kaynaklanır.

## En hızlı çözüm

1. Klasörü `C:\BDB\BunuDaBastik3D_Ecosystem_PRO` gibi Türkçe karakter içermeyen kısa bir yola taşı.
2. Eski `build` ve `dist` klasörlerini sil veya `build_windows.bat` bunu otomatik temizlesin.
3. `build_windows.bat` dosyasını çalıştır.
4. Oluşan EXE'yi sadece buradan aç:

`dist\BunuDaBastik3D-ControlCenter-PRO.exe`

## Dikkat

- `build` klasöründeki EXE çalıştırılmaz.
- Eski ONEDIR build kullanılırsa EXE tek başına kopyalanmaz, yanındaki `_internal` klasörüyle birlikte kalmalıdır.
- Kullanıcı klasörü `SELİM` gibi Türkçe karakter içeriyorsa PyInstaller bazen DLL yolunu çözemeyebilir. En güvenlisi `C:\BDB` gibi düz bir klasör kullanmaktır.

## Alternatif

Kaynak koddan çalıştırmak için:

```bat
run_windows.bat
```

Cloud Bridge için:

```bat
run_bridge_windows.bat
```
