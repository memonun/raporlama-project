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
    @media print {
      .page:empty {
        display: none;
      }
    }
    @page {
      size: A4;
      margin: 0;
    }
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: Arial, sans-serif;
      color: #333;
    }
    
    /* Page container - exactly A4 size */
    .page {
      width: 210mm;
      height: 297mm;
      position: relative;
      page-break-after: always;
      overflow: hidden;
    }
    
    /* Background wrapper for pattern pages */
    .bg-pattern {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }
    .bg-pattern img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    /* Content wrapper - above background */
    .content-wrapper {
      position: relative;
      z-index: 2;
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    /* Header */
    .header {
      background: rgba(255,255,255,0.9);
      text-align: center;
      padding: 20px;
    }
    .header-logo {
      height: 50px;
    }
    
    /* Main content area */
    .main-content {
      flex: 1;
      padding: 40px 60px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    
    /* Intro page specific */
    .intro-content {
      text-align: center;
      color: #1B3A6B;
    }
    .intro-content h1 {
      font-size: 3rem;
      margin-bottom: 20px;
    }
    .intro-content p {
      font-size: 1.3rem;
      margin-bottom: 40px;
    }
    .project-photo {
      width: 80%;
      max-width: 600px;
      height: auto;
      border-radius: 12px;
      margin: 0 auto;
      display: block;
    }
    
    /* Section divider specific */
    .divider-bg {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }
    .divider-bg img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .divider-content {
      position: relative;
      z-index: 2;
      height: 100%;
      display: flex;
      align-items: center;      /* <-- centers vertically */
      justify-content: center;
    }
    .divider-title {
      font-size: 3rem;
      /* … */
      padding: 0 40px;
    }
    
    /* Content section specific */
    .content-section h2 {
      color: #1B3A6B;
      font-size: 2.5rem;
      margin-bottom: 30px;
    }
    .content-text {
      background: rgba(255,255,255,0.95);
      padding: 30px;
      border-radius: 8px;
      line-height: 1.8;
      font-size: 1.1rem;
    }
    .content-figure {
      margin: 30px 0;
      text-align: center;
    }
    .content-figure img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
    }
    
    /* Footer */
    .footer {
      background: rgba(255,255,255,0.9);
      text-align: center;
      padding: 20px;
      font-size: 0.9rem;
      color: #666;
    }
        /* Footer logo */
      .footer-logo {
        height: 30px;
        margin-bottom: 10px;
      }

      /* Corner logo */
      .corner-logo {
        position: absolute;
        bottom: 40px;
        right: 40px;
        height: 50px;
        z-index: 3;
      }
  </style>
</head>
<body>

  <!-- INTRO PAGE -->
  <div class="page">
    <div class="bg-pattern">
      <img src="metroway_frame" alt="">
    </div>
    <div class="content-wrapper">
      <header class="header">
        <!-- header logo removed -->
      </header>
      <div class="main-content intro-content">
        <h1>V_Metroway Yatırımcı Raporu</h1>
        <p>1 Mart 2024 – 1 Mart 2025 Dönemi</p>
        <img src="metroway_foto" alt="V_Metroway Projesi" class="project-photo">
      </div>
      <!-- single corner logo on every page -->
      <img src="isra_logo" alt="İsra Logo" class="corner-logo">
      <footer class="footer">
        <!-- footer logo removed -->
        <div>© 2025 İsra Holding. Tüm hakları saklıdır.</div>
      </footer>
    </div>
  </div>

  <!-- SECTION DIVIDER PAGE -->
  <div class="page">
    <div class="divider-bg">
      <img src="kapak_foto" alt="">
    </div>
    <div class="divider-content">
      <div class="divider-title">[SECTION TITLE]</div>
    </div>
    <!-- corner logo here, too -->
    <img src="isra_logo" alt="İsra Logo" class="corner-logo">
  </div>

  <!-- CONTENT PAGE -->
  <div class="page">
    <div class="bg-pattern">
      <img src="metroway_frame" alt="">
    </div>
    <div class="content-wrapper">
      <header class="header">
        <!-- header logo removed -->
      </header>
      <div class="main-content">
        <h2>[Section Title]</h2>
        <div class="content-text">
          <p>[Content from PDF search]</p>
        </div>
        <div class="content-figure">
          <img src="[image-name]" alt="[Description]">
        </div>
      </div>
      <!-- only this one logo now -->
      <img src="isra_logo" alt="İsra Logo" class="corner-logo">
      <footer class="footer">
        <!-- footer logo removed -->
        <div>© 2025 İsra Holding.</div>
      </footer>
    </div>
  </div>

</body>
</html>
```

## IMPORTANT RULES:

1. **Use `<img>` tags for ALL images** - WeasyPrint handles img tags better than CSS backgrounds
2. **Use absolute positioning for backgrounds** - Layer content with z-index
3. **Fixed dimensions** - Use exact A4 dimensions (210mm x 297mm)
4. **No CSS background-image** - Always use img elements
5. **Structure each page as a complete unit** with the .page class

## Content Structure:

1. **Intro Page**: Company logo, report title, date, main project photo
2. **Section Dividers**: Full blue background (kapak_foto) with white section title
3. **Content Pages**: Pattern background (metroway_frame), header, content, images, footer

## 🖼️ Content images
{{images_block}}

## OUTPUT: Return ONLY the complete HTML following the template above. Use actual content from PDFs.