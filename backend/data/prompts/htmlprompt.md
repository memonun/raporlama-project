## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  

## 💼 Investor Report Template (from Vector Store)  
I want you to craft an investor report—drawing on the PDF contents in the provided vector store—in a highly polished style, as though you were the corporate communications director of a large holding company. You must inform our investors about the status of their investments in eloquent, engaging language. Organize the report under headings you find appropriate for the topics in the PDFs, and embed any relevant images in suitably designed locations. Return only the final, ready-to-use HTML. Adhere to the examples provided when creating the HTML.

## 🎨 Fixed brand assets for **{{project_slug}}**
- logo_main        → project_assets/{{project_slug}}/logo.svg  
- banner_header    → project_assets/{{project_slug}}/banner.svg  
- background_page  → project_assets/{{project_slug}}/bg-wave.svg  

`assets/styles.css` already defines:
logo{height:42px;}
.banner{height:80px;background:url(“project_assets/{{project_slug}}/banner.svg”)center/cover;}
body::before{content:””;position:fixed;inset:0;background:url(“project_assets/{{project_slug}}/bg-wave.svg”)center/cover;opacity:.05;pointer-events:none;}
Use these classes; **never inline SVG code**.

--- -->

## 🖼️ Content images (embed each once)
{{images_block}}

---

## 📑 Report outline (from PDFs via `file_search`)
{{section_block}}

---

## 📏 OUTPUT RULES  ⚠️ STRICT
1. Return **one valid HTML document**—nothing else.  
2. Use semantic tags: `<section><h2><p><figure><figcaption><img>`.  
3. Reference assets by path; do **not** inline SVG.  
4. Embed each content image exactly once inside `<figure>` with a matching `<figcaption>`.  
5. Decorative SVGs: max 6 `<path>` elements **or** use `.banner` / `.logo` classes.  
6. If a section lacks context, make **one** `file_search` call, then continue.   
7. Do **not** output JSON, Markdown, or explanations—**Final HTML only**.
8. The HTML must follow a formal, investor-relations tone (professional, data-driven, no colloquialisms).
9. Any figure, table, or claim must be backed by content returned via file_search; include inline citations immediately after the sentence that uses the data.

# Examples

**<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>1 Mart 2024 – 1 Mart 2025 Faaliyet Raporu</title>
  <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;700&family=Montserrat:wght@300;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2A3F54;
      --accent: #E9851B;
      --light-bg: #F9FAFB;
      --card-bg: #FFFFFF;
      --text: #333;
      --muted: #666;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Lora', serif;
      background: var(--light-bg);
      color: var(--text);
      line-height: 1.6;
      padding: 0 20px;
    }
    header {
      background: var(--primary);
      color: #FFF;
      text-align: center;
      padding: 60px 20px;
      margin-bottom: 40px;
      border-radius: 8px;
    }
    header h1 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 2.5em;
      letter-spacing: 4px;
    }
    header h2 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 300;
      font-size: 1.4em;
      margin-top: 10px;
      opacity: .9;
    }
    section {
      margin-bottom: 40px;
    }
    section h2 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 500;
      font-size: 1.6em;
      color: var(--primary);
      margin-bottom: 15px;
      position: relative;
    }
    section h2::after {
      content: '';
      width: 50px;
      height: 3px;
      background: var(--accent);
      display: block;
      margin-top: 5px;
      border-radius: 2px;
    }
    .card {
      background: var(--card-bg);
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      margin-top: 15px;
    }
    .card ul {
      margin: 10px 0 0 20px;
    }
    .card ul li {
      margin-bottom: 8px;
    }
    .card p {
      margin-bottom: 12px;
      color: var(--muted);
    }
    h3 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 500;
      font-size: 1.2em;
      margin-top: 20px;
      color: var(--primary);
    }
    .floor-plan {
      background: #FFF;
      border: 1px solid #DDD;
      border-radius: 6px;
      padding: 15px;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;
      overflow-x: auto;
      margin-top: 10px;
    }
    footer {
      text-align: center;
      font-size: 0.9em;
      color: var(--muted);
      padding: 20px 0;
      border-top: 1px solid #EEE;
      margin-top: 60px;
    }
  </style>
</head>
<body>

  <header>
    <h1>1 MART 2024 – 1 MART 2025</h1>
    <h2>FAALİYET RAPORU</h2>
  </header>

  <section id="acilis-oncesi">
    <h2>Açılış Öncesi Süreçler ve İnşaat</h2>
    <div class="card">
      <ul>
        <li>10 Mayıs 2022 tarihinde satın alınan Metroway AVM, müteahhidin 23 ay gecikmeli teslimi nedeniyle 1 Nisan 2024 tarihinde teslim alınabilmiştir.</li>
        <li>Metroway AVM, çözüm ortağımız ECE TR.’nin kiralama çalışmalarıyla tadilat süreci başlatılmış ve 3 Ekim 2024 tarihinde kapılarını müşterilerine açmıştır.</li>
      </ul>
    </div>
  </section>

  <section id="efektif-calismalar">
    <h2>Efektif Çalışmalar</h2>
    <div class="card">
      <h3>Yapılan Neticesinde</h3>
      <ul>
        <li>52 mağaza sayısı 66’ya çıkarıldı.</li>
        <li>14 kiosk yeri yeniden düzenlendi.</li>
        <li>5 adet soğuk hava deposu kuruldu.</li>
        <li>27 adet depo alanı oluşturuldu.</li>
      </ul>
    </div>
  </section>

  <section id="renovasyon">
    <h2>Renovasyon İmalatları</h2>
    <div class="card">
      <p>Mağaza karmaları güncellendi; yeni mimariye göre bölme duvarlar, elektrik ve mekanik sistemler yeniden projelendirildi ve uygulandı.</p>
    </div>
  </section>

  <section id="insaat-katlar">
    <h2>İnşaat İşleri</h2>

    <div class="card">
      <h3>2. Bodrum Kat</h3>
      <ul>
        <li>15 mağazadan 17 mağazaya çıkarıldı.</li>
        <li>3 kiosk yeri değiştirildi.</li>
      </ul>

      <h3>1. Bodrum Kat</h3>
      <ul>
        <li>10 mağazadan 16 mağazaya çıkarıldı.</li>
        <li>5 adet soğuk hava deposu oluşturuldu.</li>
        <li>13 adet depo alanı oluşturuldu.</li>
      </ul>

      <h3>Zemin Kat</h3>
      <ul>
        <li>11 mağazadan 15 mağazaya çıkarıldı.</li>
      </ul>

      <h3>1. Kat</h3>
      <ul>
        <li>16 mağazadan 17 mağazaya çıkarıldı.</li>
        <li>ECE TR. yönetim ofisleri kuruldu.</li>
        <li>Sinema iptal edilerek iki mağaza oluşturuldu.</li>
      </ul>

      <h3>3. Bodrum Kat</h3>
      <ul>
        <li>Teknik depo ve atölye alanları yapıldı.</li>
        <li>Personel dinlenme ve giyinme alanları hazırlandı.</li>
        <li>236 nolu mağaza Mart 2025’te bölünerek 2 mağazaya kiralandı.</li>
        <li>Bölme panel imalatları devam ediyor.</li>
      </ul>
    </div>
  </section>

  <section id="kiralama-operasyon">
    <h2>Kiralama &amp; Operasyon</h2>
    <div class="card">
      <h3>A. Kiralama</h3>
      <p>V Metroway AVM, “Aile Odaklı Komşu Kapısı” konseptiyle 3 Ekim 2024’te açıldı. 14.353 m² kiralanabilir alanda 58 sözleşme imzalandı (%88,5 doluluk). Mart 2025 itibarıyla 56 mağaza ve 5 aktif kiosk hizmet veriyor.</p>
      <p><strong>Başlıca markalar:</strong> Migros, Teknosa, Mr. Diy, Playpark, Mavi Jeans, Superstep, Armine, Tiffany & Tomato, …</p>
    </div>
  </section>

  <section id="kat-planlari">
    <h2>Kat Planları &amp; Kiracı Karması</h2>
    <div class="card floor-plan">
      <!-- Eğer gerçek görseller varsa bunlara <img> ile bağlayabilirsiniz -->
      Bahçe Katı: +103.00 → +98.00 (Eğim %13.3, L: 37.5 m)  
      Shop Storage Empty  
      SCALE: ÖLÇEK DATE: TARIH LEVEL: KOT FLOOR: KAT  
      … (detaylı mimari kod ve etiketler) …
    </div>
  </section>

  <section id="c-operasyon">
    <h2>Operasyon</h2>
    <div class="card">
      <ul>
        <li>GSM baz istasyonları (Outdoor/Indoor) kuruldu.</li>
        <li>Otopark kolon boyaları ve numaralandırma tamamlandı.</li>
        <li>11 AC Voltran, 2 DC Trugo şarj istasyonu devreye alındı.</li>
        <li>Acil çağrı butonları ve asansör içi sistemler monte edildi.</li>
        <li>Temizlik (18 kişilik ekip) ve güvenlik (20 kişilik, 12 saat vardiya) operasyonları sürüyor.</li>
      </ul>
    </div>
  </section>

  <section id="pazarlama">
    <h2>Pazarlama</h2>
    <div class="card">
      <h3>Sosyal Medya Performansı</h3>
      <ul>
        <li>15,3 milyon görüntüleme</li>
        <li>%82 takipçi kazanımı</li>
        <li>%164,3 erişim artışı (4 milyon+)</li>
        <li>%100,3 etkileşim artışı</li>
        <li>%322,6 site ziyareti artışı (76,8 bin)</li>
      </ul>
      <p>Tarih: 1 Ocak 2024 – 31 Ocak 2025</p>
    </div>
  </section>

  <footer>
    © 2025 Metroway AVM <br>
    Tüm hakları saklıdır.
  </footer>

</body>
</html>**
