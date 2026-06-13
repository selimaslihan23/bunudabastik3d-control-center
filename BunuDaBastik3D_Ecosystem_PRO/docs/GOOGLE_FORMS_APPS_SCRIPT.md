# Google Forms Entegrasyonu

Bu paket `integrations/google_forms_to_bridge.gs` dosyasında Apps Script örneği içerir.

## Kullanım

1. Google Form yanıtlarının bağlı olduğu Sheet'i aç.
2. Extensions > Apps Script bölümüne gir.
3. `google_forms_to_bridge.gs` içeriğini yapıştır.
4. `BRIDGE_URL` alanını kendi Cloud Bridge webhook adresinle değiştir.
5. Trigger ekle: `onFormSubmit` fonksiyonu, event type: On form submit.

## Cloud Bridge endpoint

```text
POST /webhook/google-forms
```

Örnek URL:

```text
https://senin-domainin.com/webhook/google-forms
```

Yerel test için:

```text
http://127.0.0.1:8787/webhook/google-forms
```

Not: Google'ın dışarıdan erişebilmesi için yerel adres yetmez; HTTPS/public URL gerekir.
