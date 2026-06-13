# Instagram DM Entegrasyonu Kurulum Notları

Bu sürüm Instagram DM mesajlarını resmi Meta altyapısı üzerinden Cloud Bridge'e düşürmek için webhook endpoint'i içerir.

## Ön koşullar

- Instagram hesabı Business veya Creator / Professional olmalı.
- Instagram hesabı bir Facebook Page'e bağlı olmalı.
- Meta Developer hesabında uygulama oluşturulmalı.
- Uygulama tarafında Instagram Messaging / Messenger API for Instagram ve Webhooks yapılandırılmalı.
- Callback URL public HTTPS olmalı. Yerel 127.0.0.1 adresini Instagram doğrudan göremez.

## Uygulamadaki adresler

Entegrasyonlar sekmesinde Public Bridge URL alanına ngrok / Cloudflare Tunnel / VPS domain adresini yaz.

Instagram DM Webhook:

```
{PUBLIC_BRIDGE_URL}/webhook/instagram
```

Verify Token:

```
bunudabastik3d_verify
```

İstersen Entegrasyonlar sekmesinden farklı bir verify token belirleyebilirsin.

## Test akışı

1. Cloud Bridge'i başlat.
2. Public HTTPS tunnel aç.
3. Public Bridge URL alanına tunnel adresini yaz.
4. Webhook adreslerini kopyala.
5. Meta Developers > Webhooks alanına Instagram DM Webhook URL ve Verify Token gir.
6. Instagram hesabına test DM gönder.
7. Uygulamada Gelen Kutusu > Cloud Bridge'den Çek butonuna bas.
8. Mesaj Instagram kaynağıyla görünür.

## Not

Bu entegrasyon resmi API mantığına göre inbound mesajı alır. Kişisel Instagram hesaplarının özel DM'lerini doğrudan çekmek için gayriresmi yöntem kullanılmaz. Güvenli ve hesap kapanma riski düşük yol resmi Meta API'dir.
