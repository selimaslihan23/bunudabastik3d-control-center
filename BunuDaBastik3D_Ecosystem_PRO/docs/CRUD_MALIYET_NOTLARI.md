# CRUD ve Maliyet Yönetimi Güncellemesi

Bu sürümde günlük kullanım için kayıt düzeltme/silme akışları eklendi.

## Eklenen ana özellikler

- Stok kartlarında seçili kaydı forma alma, güncelleme, silme.
- Stok birim maliyetini fiyatlama motoruna aktarma.
- Katalog ürünlerinde düzenleme/silme.
- Teklif, sipariş ve üretim işlerinde düzenleme/silme.
- Müşteri kartlarında düzenleme/silme.
- Mesaj şablonlarında düzenleme/silme.
- E-posta, gelen kutusu ve senkron kuyruğunda silme.
- Ayarlar sekmesine Maliyet Kalemleri / Ürün Fiyatları Yönetimi.

## Stoktan fiyatlamaya aktarma

Stok kartında birim maliyet TL/g olarak tutuluyorsa, "Birim Maliyeti Fiyatlamaya Aktar" butonu bu değeri 1000 ile çarpar ve ilgili malzeme kg maliyetine işler.

Örnek:
- PLA stok birim maliyeti: 0.65 TL/g
- Fiyatlama ayarı: 650 TL/kg

Bu güncellemeden sonra katalog, teklif ve MakerWorld fiyatlayıcı yeni maliyet değerini kullanır.

## Maliyet kalemi silme mantığı

Maliyet kalemi silindiğinde kayıt pasifleştirilir ve ilgili fiyatlama anahtarı 0 değerine alınır. Bu bilinçli yapılmıştır; yanlışlıkla silinen bir kalemin fiyatlama motorunda görünmez maliyet üretmesini engeller.

Geri dönüş için "Varsayılan Maliyetleri Geri Yükle" butonu kullanılabilir.
