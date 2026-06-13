# CRUD/COST Repair Notu

Bu sürüm, eski MVP/PRO veritabanlarından kalan eksik kolonları otomatik onarır.
Önceki sürümlerde SQLite aynı tablo varsa yeni kolonları kendiliğinden eklemediği için uygulama açılmayabilir veya bazı menüler çalışmayabilir.

## Önerilen çalıştırma

1. `run_windows_REPAIR_CRUD.bat` dosyasını çalıştırın.
2. Açılmazsa `reset_database_BACKUP_AND_START.bat` dosyasını çalıştırın. Bu işlem eski veritabanını yedekleyip temiz başlangıç yapar.

## Loglar

- `%LOCALAPPDATA%\BunuDaBastik3D\logs\app_debug.log`
- Paket klasörü içinde `logs` klasörü
