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
3. Write only the file name, never the path.  
4. Embed each content image exactly once inside `<figure>` I do not want figcaptions.  
5. Decorative SVGs: max 6 `<path>` elements **or** use `.banner` / `.logo` classes.  
6. If a section lacks context, make **one** `file_search` call, then continue.   
7. Do **not** output JSON, Markdown, or explanations—**Final HTML only**.
8. The HTML must follow a formal, investor-relations tone (professional, data-driven, no colloquialisms).
9. Any figure, table, or claim must be backed by content returned via file_search; include inline citations immediately after the sentence that uses the data.

## 🎨 V_Metroway Specific Design Rules

### Namings
- Just place the image names in the HTML no path references or else they will be handled afterwards. So the true naming and proper placement is critical
### Section Dividers
- Use `kapak_foto.svg` (full blue cover) between major sections:
  - Since you are determining the sections according to the content provided, this will just be an example; between sections like Financial State, Construction Status etc. Use this svg like a transition page and include the header on the svg.

### Background Pattern
- Apply `metroway_frame.svg` as background for all content sections

### Logo Placement
- Place `isra_logo.png` in header and footer
- Place `isra_logo.png` in bottom-right corner of major sections

### First Page
- After the logo placement u should utilize the `metroway_foto.jpg` as a big photo of the project at the cover page.  

### Color Scheme

- Primary Blue: #1B3A6B 
- Accent Red: #E4242B 
- Background: #F5F5F5
- Text: #333333

### Example
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>V_Metroway Yatırımcı Raporu</title>
  <style>
    body {
      margin: 0;
      background: #F5F5F5;
      font-family: Arial, sans-serif;
      color: #333;
    }
    .page {
      width: 100%;
      min-height: 100vh;         /* full viewport */
      position: relative;
      page-break-after: always;
    }
    .content-section{
    background: #fff url('metroway_frame.svg') center/cover no-repeat;
    }
    /* Header & Footer */
    .header, .footer {
      background: #fff;
      text-align: center;
    }
    .header {
      padding: 1.5rem 0 1rem;
      border-bottom: 1px solid #ddd;
    }
    .header-logo { height: 50px; }
    .footer {
      position: absolute;
      bottom: 1rem;
      width: 100%;
      font-size: 0.85rem;
      color: #666;
    }
    .footer-logo { height: 40px; margin-bottom: 0.5rem; }
    .intro-page {
      background: url('metroway_frame.svg') center center / cover no-repeat !important;
      color: #1B3A6B;
      text-align: center;
      padding-top: 6rem;
    }
    .intro-page h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .intro-page p  { font-size: 1.2rem; }
    .main-photo {
      display: block;
      width: 80%; max-width: 900px;
      margin: 2rem auto 0;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(27,58,107,0.08);
    }
    .section-divider {
      background: url('kapak_foto.svg') center center / cover no-repeat !important;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .section-divider .header {
      background: transparent;
      padding-top: 2rem;
      border: none;
    }
    .divider-title {
      margin: auto 0;
      font-size: 2.2rem;
      color: #fff;
      font-weight: 700;
      letter-spacing: 2px;
      text-shadow: 0 2px 8px rgba(27,58,107,0.25);
      text-transform: uppercase;
      text-align: center;
    }
    .content-section {
      background: #fff url('metroway_frame.svg') center center / cover no-repeat !important;
      margin: 2rem auto;
      padding: 2.5rem 2rem 4rem;
      max-width: 900px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      min-height: 80vh;
    }
    .content-section h2 {
      color: #1B3A6B;
      margin-bottom: 1.2rem;
      font-size: 2rem;
    }
    .content-section p, .content-section ul {
      line-height: 1.7;
      margin-bottom: 1.2rem;
    }
    .content-section ul li {
      margin-left: 1.2rem;
      list-style: disc;
    }
    .section-logo {
      position: absolute;
      bottom: 2rem;
      right: 2rem;
      height: 48px;
      opacity: 0.85;
    }
    figure {
      margin: 2rem auto;
      text-align: center;
    }
    figure img {
      display: block;
      margin: 0 auto;
      max-width: 95%;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(27,58,107,0.10);
    }
  </style>
</head>
<body>

  <!-- Page 1: Intro -->
  <section class="page intro-page">
    <header class="header">
      <img src="isra_logo.png" alt="İsra Logo" class="header-logo">
    </header>
    <h1>V_Metroway Yatırımcı Raporu</h1>
    <p>1 Mart 2024 – 1 Mart 2025 Dönemi</p>
    <figure>
      <img src="metroway_foto.jpg" alt="Proje Fotoğrafı" class="main-photo">
    </figure>
    <footer class="footer">
      <img src="isra_logo.png" alt="Footer Logo" class="footer-logo"><br>
      © 2025 İsra Holding. Tüm hakları saklıdır.
    </footer>
  </section>

  <!-- Page 2: Divider -->
  <section class="page section-divider">
    <header class="header">
      <img src="isra_logo.png" alt="İsra Logo" class="header-logo">
    </header>
    <div class="divider-title">Finansal Durum</div>
  </section>

  <!-- Page 3: Content -->
  <section class="page content-section">
    <header class="header">
      <img src="isra_logo.png" alt="İsra Logo" class="header-logo">
    </header>
    <h2>Finansal Durum</h2>
    <p>2024 net kâr: 12.500.000 TL; 2025 projeksiyonu: 18.000.000 TL. AVM kiralama, tatil köyü, ticari işletmelerle güçlü nakit akışı.</p>
    <figure>
      <img src="finans-1750769809.webp" alt="Finans Çizelge">
    </figure>
    <img src="isra_logo.png" alt="İsra Logo" class="section-logo">
    <footer class="footer">
      <img src="isra_logo.png" alt="Footer Logo" class="footer-logo"><br>
      © 2025 İsra Holding.
    </footer>
  </section>

  <!-- …other pages… -->

</body>
</html>


### Section Structure
```html
<!-- Major Section Divider -->
<div class="section-divider">
  <img src="kapak_foto.svg" alt="" />
</div>

<!-- Content Section -->
<section class="content-section"
         style="background:#fff url('metroway_frame.svg') center/cover no-repeat;">
  <!-- Content here -->
</section>



