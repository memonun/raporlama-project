## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  

## 💼 Investor Report Template (from Vector Store)  
Create an investor report for V_Metroway project using content from the PDFs. Write in a polished, professional style as the corporate communications director of İsra Holding.

## 🎨 V_Metroway Design Requirements

### CRITICAL: Use WeasyPrint-compatible HTML structure

The PDF generator has limitations. You MUST follow this exact structure for proper rendering:

### Required Files (use ONLY these exact names, no extensions or paths):
- `kapak_foto` - Blue section divider background
- `metroway_frame` - Pattern background  
- `isra_logo` - Company logo
- `metroway_foto` - Main project photo

### Page Structure Template:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>V_Metroway Yatırımcı Raporu</title>
<style>
  /* --- GLOBAL --- */
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#F5F5F5;font-family:Arial,sans-serif;color:#333}
  .page{width:100%;min-height:100vh;position:relative;page-break-after:always;overflow:hidden}

  /* header & footer (repeat) */
  .header,.footer{background:#fff;text-align:center}
  .header{padding:1.5rem 0 1rem;border-bottom:1px solid #ddd}
  .header-logo{height:50px}
  .footer{position:absolute;bottom:1rem;width:100%;font-size:.85rem;color:#666}
  .footer-logo{height:40px;margin-bottom:.5rem}

  /* intro */
  .intro-page{background:url('metroway_frame.svg') center/cover no-repeat;color:#1B3A6B;text-align:center;padding-top:6rem}
  .intro-page h1{font-size:2.5rem;margin-bottom:.5rem}
  .intro-page p{font-size:1.2rem}
  .main-photo{display:block;width:80%;max-width:900px;margin:2rem auto 0;border-radius:12px;box-shadow:0 2px 12px rgba(27,58,107,.08)}

  /* divider */
  .section-divider{background:url('kapak_foto.svg') center/cover no-repeat;min-height:100vh;position:relative}
  .section-divider .header{background:transparent;border:none;padding-top:2rem}
  .divider-title{
      position:absolute;left:0;right:0;top:60%;                /* ← 2/5 of page height */
      transform:translateY(-50%);
      font-size:2.2rem;color:#fff;text-align:center;font-weight:700;
      letter-spacing:2px;text-transform:uppercase;
      text-shadow:0 2px 8px rgba(27,58,107,.25)
  }
    .header {display: none !important;}
  /* content */
  .content-section{
      margin:2rem auto;padding:2.5rem 2rem 4rem;max-width:900px;
      border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);min-height:80vh
  }
  .content-section h2{color:#1B3A6B;font-size:2rem;margin-bottom:1.2rem}
  .content-section p{line-height:1.7;margin-bottom:1.2rem}
  .section-logo { display: none !important;}/* only used in content pages */

  /* images */
  figure{margin:2rem auto;text-align:center}
  figure img{display:block;margin:0 auto;max-width:95%;border-radius:8px;box-shadow:0 2px 8px rgba(27,58,107,.1)}
</style>
</head>
<body>

<!-- PAGE 1 – INTRO -->
<section class="page intro-page">
  <header class="header"><img src="isra_logo.png" alt="İsra Logo" class="header-logo"></header>
  <h1>V_Metroway Yatırımcı Raporu</h1>
  <p>1 Mart 2024 – 1 Mart 2025 Dönemi</p>
  <figure><img src="metroway_foto.jpg" alt="Proje Fotoğrafı" class="main-photo"></figure>
  <footer class="footer"><img src="isra_logo.png" class="footer-logo" alt=""><br>© 2025 İsra Holding.</footer>
</section>

<!-- PAGE 2 – DIVIDER -->
<section class="page section-divider">
  <h2 class="divider-title">Proje Genel Bakış</h2>
</section>

<!-- PAGE 3 – CONTENT -->
<section class="page content-section">
  <header class="header"><img src="isra_logo.png" class="header-logo" alt=""></header>
  <h2>Finansal Durum</h2>
  <p>2024 net kâr: 12 500 000 TL &nbsp;•&nbsp; 2025 projeksiyonu: 18 000 000 TL.</p>
  <figure><img src="finans-1750769809.webp" alt=""></figure>
  <img src="isra_logo.png" class="section-logo" alt="">
  <footer class="footer"><img src="isra_logo.png" class="footer-logo" alt=""><br>© 2025 İsra Holding.</footer>
</section>

<!-- …devam eden sayfalar… -->

</body>
</html>
```

## IMPORTANT RULES:

1. **Use `<img>` tags for ALL images** - WeasyPrint handles img tags better than CSS backgrounds
2. **Use absolute positioning for backgrounds** - Layer content with z-index
3. **Fixed dimensions** - Use exact A4 dimensions (210mm x 297mm)
4. **No CSS background-image** - Always use img elements
5. **Structure each page as a complete unit** with the .page class
6. **Always include the images that are sent with the previous response**
7. **Do not create any <section class="page"> element** unless it contains visible content (intro, divider, or content block).
8. **Divider pages (.page.section-divider)** must omit the entire <header> element.


## Content Structure:

1. **Intro Page**: Company logo, report title, date, main project photo
2. **Section Dividers**: Full blue background (kapak_foto) with white section title
3. **Content Pages**: Pattern background (metroway_frame), header, content, images, footer

## 🖼️ Content images
{{images_block}}

## OUTPUT: Return ONLY the complete HTML following the template above. Use actual content from PDFs.