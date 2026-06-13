# Kurulum Adımları

## 1. Masaüstü uygulamayı çalıştır

`run_windows.bat` dosyasını aç. İlk açılışta sanal ortam kurulur ve paketler yüklenir.

## 2. Cloud Bridge'i çalıştır

`run_bridge_windows.bat` dosyasını aç. Varsayılan adres:

```text
http://127.0.0.1:8787
```

Masaüstü uygulama `Entegrasyonlar` sekmesinde bu adrese bağlanır.

## 3. İnternetten webhook almak

WhatsApp ve Google Forms gibi dış sistemlerin senin bilgisayarına ulaşması için herkese açık HTTPS gerekir. Seçenekler:

- VPS üzerinde Cloud Bridge çalıştırmak
- Cloudflare Tunnel
- ngrok
- Kendi domain + HTTPS reverse proxy

## 4. Odoo

Odoo ayarlarını `Entegrasyonlar` sekmesine gir:

- Odoo URL: `https://bunudabastik3d.odoo.com`
- Database adı
- Kullanıcı e-posta
- API Key

## 5. Kullanım akışı

```text
Dış kanal / yerel iş → Gelen Kutusu → Teklif → Sipariş → Üretim → Stok → Odoo
```
