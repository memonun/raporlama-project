## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  

## 💼 Investor Report Template (from Vector Store)  
Create an investor report for V_Metroway project using content from the PDFs. Write in a polished, professional style as the corporate communications director of İsra Holding. The text should satisfy in the generate report.

## 🎨 V_Metroway Design Requirements

### Required Files (use ONLY these exact names, no extensions or paths):
- `kapak_foto` - Blue section divider background
- `metroway_frame` - Pattern background  
- `isra_logo` - Company logo
- `metroway_foto` - Main project photo

### Page Structure Example:(Just as inspiration dont do the exact but i want somewhat similar content, u should follow the rules strictly not this example)

```html
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>V_Metroway Yatırımcı Raporu</title>
<style>
  /* --- GLOBAL --- */
  .bg-full{
  position:absolute;
  top:0; left:0;
  width:100%; height:100%;
  object-fit:cover;       /* stretch while preserving aspect */
  z-index:-1;             /* sit behind everything */
}
/* page padding so text isn't flush to edges */
.content-page{
  padding:90px 60px 80px;   /* top / sides / bottom */
}

/* title & body text styles (keep / tweak as needed) */
.content-page h2{font:700 32px/1 Arial,sans-serif;color:#1B3A6B;margin-bottom:25px}
.content-page p{font-size:16px;line-height:1.7;color:#444;margin-bottom:20px}

/* centred figure styling */
.content-page figure{margin:30px auto;text-align:center}
.content-page figure img{max-width:95%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1)}

/* single bottom-right logo */
.corner-logo{
  position:absolute;
  right:60px; bottom:80px;
  height:48px; opacity:.85;
}

/* safety-net: ensure no stray header / footer shows here */
.content-page .header,
.content-page .footer{display:none!important;}

/* lower-half title */
.divider-title{
  position:absolute;
  left:0; right:0;
  top:60%;                /* 60 % down the page */
  transform:translateY(-40%);
  font:700 42px/1 Arial, sans-serif;
  letter-spacing:2px;
  text-transform:uppercase;
  color:#fff;
  text-align:center;
  text-shadow:0 3px 10px rgba(0,0,0,.3);
}

/* ensure no header or corner logo gets rendered here */
.section-divider .header,
.section-divider .section-logo{display:none!important;}

 
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

  <!-- full-bleed background image -->
  <img src="kapak_foto" alt=""
       class="bg-full">

  <!-- centred heading, visually in bottom-half -->
  <h2 class="divider-title">Proje Genel Bakış</h2>
</section>

<!-- PAGE 3 – CONTENT -->
<section class="page content-page">

  <!-- ① full-page frame -->
  <img src="metroway_frame" alt="" class="bg-full">

  <!-- ② your actual content -->
  <h2>Finansal Durum</h2>
  <p>{Fill with provided content from PDFs}</p>

  <figure>
    <img src="finans-1750769809.webp" alt="Finansal Grafik">
  </figure>

  <!-- ③ single bottom-right logo -->
  <img src="isra_logo" alt="" class="corner-logo">

</section>

<!-- …devam eden sayfalar… -->

</body>
</html>
```
 **Additional css styling as you wish to make the document very delecate but dont conflict my rules**

## IMPORTANT RULES:

1. **Use `<img>` tags for ALL images** - WeasyPrint handles img tags better than CSS backgrounds
2. **Use absolute positioning for backgrounds** - Layer content with z-index
3. **Fixed dimensions** - Use exact A4 dimensions (210mm x 297mm)
4. **No CSS background-image** - Always use img elements
5. **Structure each page as a complete unit** with the .page class
6. **Always include the images that are sent with the previous response**
7. **Do not create any <section class="page"> element** unless it contains visible content (intro, divider, or content block).
8. **Divider pages (.page.section-divider)** must omit the entire <header> element.




## 🖼️ Content images
{{images_block}}

## OUTPUT: Return ONLY the complete HTML following the template above. Use actual content from PDFs.