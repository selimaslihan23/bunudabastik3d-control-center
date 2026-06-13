# Katalog Fiyat Hesaplama Düzeltmesi

Bu sürümde katalog fiyatlayıcıya iki yeni seçenek eklendi:

- Gram tipi: Parça başı / Toplam
- Süre tipi: Toplam / Parça başı

## Neden eklendi?

MakerWorld veya Bambu Studio bazı durumlarda süreyi plakanın toplam süresi olarak verir. Uygulama bunu parça başı süre sanıp adetle tekrar çarparsa fiyat gereğinden yüksek çıkar.

Örnek:

- Adet: 100
- Gram: 10
- Süre: 660 dk
- Gram tipi: Parça başı
- Süre tipi: Toplam

Bu durumda hesap 1000 g ve 660 dk üzerinden yapılır.

Eğer süre 1 ürünün süresiyse Süre tipi = Parça başı seçilmelidir.
