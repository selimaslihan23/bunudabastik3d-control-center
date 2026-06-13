# WhatsApp Business Cloud API Entegrasyonu

Normal WhatsApp Business uygulaması, gelen mesajları doğrudan masaüstü uygulamaya webhook olarak göndermez. Otomatik entegrasyon için Meta WhatsApp Business Platform / Cloud API gerekir.

## Cloud Bridge endpointleri

Doğrulama:

```text
GET /webhook/whatsapp
```

Mesaj alma:

```text
POST /webhook/whatsapp
```

## Ortam değişkeni

Cloud Bridge çalışırken verify token:

```bat
set WHATSAPP_VERIFY_TOKEN=bunudabastik3d_verify
```

Meta Developer panelinde webhook doğrulama token'ı aynı değer olmalı.

## Notlar

- Gerçek kullanımda HTTPS zorunludur.
- Müşteri konuşmaları, izin ve mesaj şablonu kurallarına bağlıdır.
- Dosya/medya mesajları bu sürümde medya ID olarak kaydedilir; dosya indirme sonraki sürüm modülüdür.
