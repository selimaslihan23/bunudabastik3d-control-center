# Gmail OAuth Kurulumu

Bu sürümde Gmail artık sadece App Password / IMAP ile değil, Google hesabı üzerinden OAuth ile bağlanabilir.

## 1. Google Cloud projesi oluştur

1. https://console.cloud.google.com/ adresine gir.
2. Yeni bir proje oluştur: `BunuDaBastik3D Control Center`.
3. `APIs & Services` bölümünden **Gmail API** servisini etkinleştir.

## 2. OAuth ekranını hazırla

1. `Google Auth platform` veya `OAuth consent screen` bölümüne gir.
2. Kullanıcı türü olarak genelde **External** seçilir.
3. Uygulama adı: `BunuDaBastik3D Control Center`.
4. Test aşamasındaysa kendi Gmail adresini **Test users** kısmına ekle.

## 3. Desktop OAuth istemcisi oluştur

1. `Clients / Credentials` bölümüne gir.
2. `Create OAuth client ID` seç.
3. Uygulama türü: **Desktop app**.
4. JSON dosyasını indir.
5. İndirdiğin dosya genelde `client_secret_....json` gibi görünür. Uygulamada bu dosyayı seçeceksin.

## 4. Uygulamada bağlan

1. BunuDaBastık3D uygulamasını aç.
2. `E-Posta` sekmesine gir.
3. `credentials.json Seç` butonuna bas ve Google'dan indirdiğin JSON dosyasını seç.
4. `Gmail ile Bağlan / Yetki Ver` butonuna bas.
5. Tarayıcıda Google giriş ekranı açılır.
6. İzin ver.
7. Uygulamaya dönüp `Gmail API Mailleri Çek` butonuna bas.

## 5. Arama kutusu

Varsayılan arama:

```text
in:inbox
```

Örnekler:

```text
in:inbox newer_than:30d
from:example@gmail.com
subject:(3d OR baskı)
has:attachment
```

## Güvenlik notu

- Google hesabı şifreni uygulamaya yazma.
- Uygulama sadece Gmail okuma yetkisi ister: `gmail.readonly`.
- Token dosyası yerel kullanıcı veri klasörüne kaydedilir.
- Yetkiyi kaldırmak için uygulamadaki `OAuth Yetkisini Sıfırla` butonunu kullanabilirsin.

## Hata alırsan

- `credentials.json bulunamadı`: Önce JSON dosyasını seç.
- `access blocked / test user`: Google Cloud OAuth ekranında kendi Gmail adresini test user olarak ekle.
- `API not enabled`: Google Cloud projesinde Gmail API'yi etkinleştir.
- Tarayıcı açıldı ama dönmüyorsa: Güvenlik duvarı veya tarayıcı localhost dönüşünü engelliyor olabilir. Tekrar dene.
