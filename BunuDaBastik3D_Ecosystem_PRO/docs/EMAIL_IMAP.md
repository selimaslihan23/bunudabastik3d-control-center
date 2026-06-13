# E-posta Entegrasyonu

Uygulamada `E-Posta` sekmesi vardır. IMAP ile gelen mailleri çekip otomatik olarak Gelen Kutusu'na talep olarak ekleyebilir.

## Gmail için

Gmail hesabında iki aşamalı doğrulama açıksa App Password kullanman gerekir. Normal Gmail şifreni yazma.

Örnek ayarlar:

```text
IMAP Host: imap.gmail.com
Port: 993
Mailbox: INBOX
```

## Özel domain e-posta için

Hosting sağlayıcının IMAP bilgilerini kullan:

```text
mail.senin-domainin.com
993
```

## Güvenlik

E-posta parolası yerel SQLite ayarlarında saklanır. Daha güvenli sürüm için Windows Credential Manager entegrasyonu eklenebilir.
