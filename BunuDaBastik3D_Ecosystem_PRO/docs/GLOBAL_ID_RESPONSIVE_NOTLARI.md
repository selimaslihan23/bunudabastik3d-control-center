# Global ID / Sıralama ve Responsive Ekran Notları

Bu sürümde uygulamaya yeni **Kayıt Sıralama** sayfası eklendi.

## Kapsam
Bu merkezden aşağıdaki modüllerin ID ve sıralama değerleri yönetilebilir:

- Gelen Kutusu
- E-Posta
- Teklifler
- Katalog
- Siparişler
- Üretim
- Stok
- Müşteriler
- Mesajlar
- Maliyet Kalemleri

## Sıralama Mantığı
Listelerde `sort_order` değeri büyük olan kayıt üstte görünür.

Butonlar:

- **Yukarı Taşı:** kaydı bir üst sıraya alır.
- **Aşağı Taşı:** kaydı bir alt sıraya alır.
- **En Üste Al:** kaydı listenin en üstüne taşır.
- **En Alta Al:** kaydı listenin en altına taşır.
- **Sıra Kaydet:** elle girilen sıra değerini kaydeder.

## ID Değiştirme
ID değiştirmek için:

1. Modül seçilir.
2. Kayıt seçilir.
3. Yeni ID yazılır.
4. **ID değişimini onaylıyorum** kutusu işaretlenir.
5. **ID Değiştir** butonuna basılır.

Bilinen ilişkiler otomatik taşınır:

- Gelen Kutusu → Teklifler / E-postalar
- Teklifler → Siparişler
- Siparişler → Üretim işleri

## Taşma / Sığmama Düzeltmesi
Bu sürümde:

- Uygulama ekrana göre açılır.
- Windows’ta pencere otomatik büyütülür.
- Ana içerik sayfaları dikey kaydırma destekler.
- Sol menü de kaydırılabilir hale getirildi.

Küçük ekranlarda içerik artık pencere dışına taşmak yerine scroll ile kullanılabilir.
