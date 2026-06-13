

## CRUD/COST Repair Sürümü

Stok, katalog, teklif, sipariş, üretim, müşteri ve maliyet kalemlerinde düzenle/sil özellikleri eklendi.
Eski sürüm veritabanı varsa önce şu dosyayı çalıştırın:

```bat
run_windows_REPAIR_CRUD.bat
```

Hâlâ açılmazsa eski veritabanını yedekleyip temiz başlangıç için:

```bat
reset_database_BACKUP_AND_START.bat
```

# BunuDaBastık3D Control Center PRO

Bu paket, BunuDaBastık3D için masaüstü kontrol paneli + Cloud Bridge entegrasyon iskeletidir.

## Ana yetenekler

- Tek panelden gelen işler: WhatsApp Cloud API, Google Forms, e-posta, web formları, yerel işler
- Gelen Kutusu sekmesi
- E-Posta sekmesi: IMAP ile gelen mailleri çekme ve talebe dönüştürme
- Otomatik ön teklif: gramaj + destek gramajı + baskı süresi + adet
- Katalog fiyatlayıcı: MakerWorld link + manuel gram/süre
- Sipariş, üretim, stok, müşteri, mesaj şablonu yönetimi
- Üretim tamamlanınca stoktan filament düşme
- Odoo CRM/Product senkron kuyruğu
- Excel dışa aktarma ve veritabanı yedekleme

## Hızlı başlatma

1. ZIP'i çıkar.
2. `run_windows.bat` dosyasını çalıştır.
3. Uygulama açılınca `Entegrasyonlar` ve `Ayarlar` sekmelerini doldur.
4. Cloud Bridge için ikinci bir terminalde `run_bridge_windows.bat` çalıştır.

## Windows exe üretme

Masaüstü uygulama:

```bat
build_windows.bat
```

Cloud Bridge:

```bat
build_bridge_windows.bat
```

Çıktılar `dist` klasörüne düşer.

## Güvenlik

API key, e-posta app password ve webhook secret bilgilerini kimseyle paylaşma. WhatsApp / Google webhook'ları için gerçek kullanımda HTTPS domain gerekir.


## v3.0 Premium UI Ekleri

Bu pakette logo görseli uygulamanın sol menüsüne, pencere ikonuna ve açılış/giriş akışına entegre edildi.

Eklenen arayüz özellikleri:
- Splash screen
- Operatör giriş ekranı
- Mor/siyah premium tema
- Dashboard hızlı işlem barı
- Klavye kısayolları
- Premium önizleme görselleri

Detaylar için: `docs/ARAYUZ_PREMIUM_NOTLARI.md`

## Python DLL hatası alırsan

`Failed to load Python DLL ... python314.dll` görürsen `FIX_PYTHON_DLL_HATASI.md` dosyasındaki adımları uygula. Kısa çözüm: klasörü `C:\BDB` gibi Türkçe karakter içermeyen bir yere taşı ve `build_windows.bat` ile temiz build al.

## SAFE MODE

Normal premium arayüz arka planda çalışıyor ama pencere görünmüyorsa:

```bat
run_windows_SAFE.bat
```

EXE üretmek için:

```bat
build_windows_SAFE_DEBUG.bat
```

Çıkan EXE:

```text
dist\BunuDaBastik3D-ControlCenter-SAFE\BunuDaBastik3D-ControlCenter-SAFE.exe
```

## FINAL STABLE UI

Bu pakette Safe Mode çekirdeği varsayılan başlatma modu oldu. Uygulama direkt ana panele açılır ve Ayarlar sekmesinden Selim/Kemal operatör seçimi, tema, arka plan efekti, buton stili ve animasyon seviyesi değiştirilebilir.

Çalıştırma:

```bat
run_windows.bat
```

EXE üretme:

```bat
build_windows_FINAL_STABLE.bat
```

Debug EXE üretme:

```bat
build_windows_FINAL_STABLE_DEBUG.bat
```

## CRUD + Maliyet Yönetimi Sürümü

Bu pakette stok, katalog, teklifler, siparişler, üretim, müşteriler ve mesaj şablonları için düzenle/sil akışları eklendi. Ayarlar sekmesinde maliyet kalemleri yönetilebilir. Stok kartındaki TL/g birim maliyet, tek tuşla fiyatlama motorundaki TL/kg maliyetlere aktarılabilir.

## Gmail OAuth eklentisi

E-Posta sekmesine `Gmail OAuth bağlantısı` alanı eklendi. App Password görünmeyen Google hesaplarında bu yöntemi kullanın.
Kurulum adımları için: `docs/GMAIL_OAUTH_KURULUM.md`

## FINAL CONNECTOR Güncellemesi

Bu pakette Entegrasyonlar sayfası güçlendirildi:

- Cloud Bridge uygulama içinden başlatılabilir/durdurulabilir.
- Gmail, Instagram DM, Google Forms, WhatsApp, Odoo durum kartları eklendi.
- Public Bridge URL alanı eklendi.
- Instagram DM webhook endpoint'i eklendi: `/webhook/instagram`.
- Gelen kutusu ve e-posta kayıtları büyük içerik penceresinde açılabilir ve kopyalanabilir.
- Entegrasyon logları uygulama içinde görüntülenebilir.

Instagram DM için resmi Meta kurulumu gerekir. Detay: `docs/INSTAGRAM_DM_KURULUM.md`.

## FINAL API CENTER güncellemesi

Bu pakette sol menüye **API Ayarları** ve **Hammadde Fiyat Merkezi** eklendi.

- API Ayarları: Gmail, Instagram DM, WhatsApp Business, Google Forms, Odoo ve Cloud Bridge için ayrı sekmeler.
- Hammadde Fiyat Merkezi: PLA/PETG/ABS/ASA/TPU/Support maliyetlerini tek yerden günceller ve tüm fiyatlama motoruna uygular.


## Hammadde Fiyat Merkezi güncellemesi

Hammadde Fiyat Merkezi artık filament kg fiyatları yanında Minimum Fiyat, İşçilik, Son İşlem, Paketleme, Fire, KDV ve Komisyon alanlarını da içerir. Oranlar katsayı olarak girilir: 0.20 = %20, 0.70 = %70.

## v3.2 GLOBAL ID + Responsive Hotfix

- Yeni sol menü: **Kayıt Sıralama**
- Ana modüllerde global ID ve sıra yönetimi
- Üretim, katalog, stok, sipariş, teklif, müşteri vb. kayıtlar için merkezi sıra düzeltme
- Pencere dışına taşma/sığmama problemleri için otomatik ekran uyumu
- Sayfa içi dikey kaydırma ve sol menü scroll desteği
