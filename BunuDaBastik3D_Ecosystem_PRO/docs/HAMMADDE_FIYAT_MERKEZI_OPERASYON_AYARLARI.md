# Hammadde Fiyat Merkezi - Operasyon Ayarları

Bu sürümde Hammadde Fiyat Merkezi sadece filament kg fiyatlarını değil, teklif hesabını etkileyen temel operasyon ayarlarını da tek yerden yönetir.

## Eklenen alanlar

- Minimum fiyat: `250`
- İşçilik: `60`
- Son işlem: `40`
- Paketleme: `25`
- Fire / başarısız baskı payı: `0.12`
- KDV: `0.20`
- Komisyon: `0`
- Makine saat ücreti: önerilen başlangıç `60`
- Kâr oranı: önerilen başlangıç `0.70`

## Oran alanları nasıl yazılır?

Oran alanları yüzde işaretiyle yazılmaz. Katsayı olarak yazılır.

- `0.12` = %12
- `0.20` = %20
- `0.70` = %70
- `1.00` = %100

`70` yazmak %7000 anlamına gelir ve fiyatı anormal yükseltir.

## Nereleri etkiler?

Kaydettiğinde şu hesaplar yeni değerlerle çalışır:

- Katalog fiyatlayıcı
- Teklif fiyatı
- Siparişe dönüşen maliyetler
- Stok kartlarındaki filament birim maliyetleri
- Ayarlar > Maliyet kalemleri
