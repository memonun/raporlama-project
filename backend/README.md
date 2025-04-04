# Yatırımcı Raporu Backend

## E-posta Görselleri

E-posta şablonunda kullanılmak üzere aşağıdaki görsel dosyalarını `backend/static/assets/` klasörüne eklemeniz gerekmektedir:

1. **Logo Görseli:**
   - Dosya adı: `logo.png`
   - Önerilen boyut: 150x60 piksel
   - Şirket logonuzu bu dosya olarak kaydedin
   - Format: PNG (şeffaf arkaplan için) veya JPG

2. **Kapak Görseli:**
   - Dosya adı: `cover.jpg`
   - Önerilen boyut: 600x200 piksel
   - E-postanın üst kısmında görüntülenecek görseli bu dosya olarak kaydedin
   - Format: JPG veya PNG

### Görselleri Ekleme Adımları

1. `backend/static/assets/` klasörünü oluşturun (yoksa):
   ```
   mkdir -p backend/static/assets
   ```

2. Logo ve kapak görsellerinizi bu klasöre şu şekilde kopyalayın:
   ```
   cp logo.png backend/static/assets/
   cp cover.jpg backend/static/assets/
   ```

3. Görsel dosyalarının izinlerini kontrol edin:
   ```
   chmod 644 backend/static/assets/*.{png,jpg}
   ```

### Notlar

- Eğer belirtilen dosyalar bulunamazsa, e-posta görselsiz olarak gönderilecektir.
- Görsel boyutlarını önerilen değerlere yakın tutmanız, e-posta görünümünün en iyi şekilde olmasını sağlayacaktır.
- Logonun PNG formatında ve şeffaf arkaplanla kaydedilmesi önerilir.
- Kapak görseli için kaliteli bir JPG dosyası önerilir.

## Örnek E-posta Görünümü

Doğru şekilde ayarlandığında, e-posta alıcılara şu şekilde görünecektir:

```
+------------------------------------------+
|                                          |
|              [ŞİRKET LOGO]               |
|                                          |
|          [KAPAK GÖRSELİ/RESMİ]           |
|                                          |
+------------------------------------------+
|                                          |
| Sayın İlgili,                            |
|                                          |
| [PROJE ADI] için yatırımcı raporundaki   |
| eksik bilgilerin tamamlanması rica       |
| olunur, iyi çalışmalar.                  |
|                                          |
| Saygılarımızla,                          |
| İSRA HOLDİNG                             |
|                                          |
+------------------------------------------+
| Yardım: israreport@israholding.com.tr    |
| © 2023 İSRA HOLDİNG. Tüm hakları saklıdır|
+------------------------------------------+
``` 