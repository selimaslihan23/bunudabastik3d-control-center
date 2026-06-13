# Güvenlik Notları

- API key, e-posta app password, webhook secret ve Odoo bilgilerini paylaşma.
- WhatsApp ve Google webhook için HTTPS kullan.
- Cloud Bridge'i public internete açacaksan `BDB_WEBHOOK_SECRET` kullan.
- E-posta parolaları bu MVP/PRO pakette yerel SQLite içinde saklanır.
- Canlı üretim sürümünde Windows Credential Manager, şifreleme veya server-side secrets kullanılmalıdır.

## Webhook Secret

Cloud Bridge'i secret ile başlatmak için:

```bat
set BDB_WEBHOOK_SECRET=uzun-bir-gizli-anahtar
```

Dış sistemler POST isteğinde şu header'ı göndermeli:

```text
x-bdb-secret: uzun-bir-gizli-anahtar
```
