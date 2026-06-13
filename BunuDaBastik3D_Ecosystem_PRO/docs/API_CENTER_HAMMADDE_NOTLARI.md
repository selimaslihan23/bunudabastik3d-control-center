# BunuDaBastık3D API Center + Hammadde Fiyat Merkezi

Bu sürümde sol menüye iki yeni ana alan eklendi.

## API Ayarları

Her API artık tek kalabalık ekranda değil, ayrı sekmelerde yönetilir:

- Genel Durum
- Gmail API
- Instagram DM API
- WhatsApp Business API
- Google Forms API
- Odoo API
- Cloud Bridge API
- Webhook Yöneticisi
- API Logları

Her sayfada anlaşılır alanlar, test butonları ve kopyalama aksiyonları bulunur. Public URL gerektiren servisler için Cloud Bridge URL ve Public Bridge URL ayrılmıştır.

## Hammadde Fiyat Merkezi

PLA, PETG, ABS, ASA, TPU ve Support filament kg fiyatları artık tek merkezden değişir.

Kaydet ve Uygula butonu şunları yapar:

1. Fiyatlama motorunun ayarlarını günceller.
2. cost_items tablosundaki ilgili maliyet kalemlerini aktif şekilde günceller.
3. Stok kartlarındaki aynı malzemeye ait birim maliyetleri TL/g olarak yeniden hesaplar.
4. Katalog ve teklif hesapları yeni maliyetleri kullanır.

Örnek: PLA kg fiyatı 650 TL ise stok kartlarında PLA birim maliyeti 0.65 TL/g olur.

## Önerilen kullanım

1. Önce Hammadde Fiyat Merkezi'nden gerçek filament kg fiyatlarını gir.
2. Stok kartlarında malzeme türlerinin PLA/PETG/ABS/ASA/TPU/SUPPORT olarak doğru yazıldığını kontrol et.
3. Katalog veya teklif oluştururken malzeme seçimi bu anahtarlarla eşleşirse doğru fiyat hesaplanır.
4. API Ayarları > Genel Durum sekmesinden entegrasyonların durumunu kontrol et.
