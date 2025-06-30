## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  

## 💼 Investor Report Template (from Vector Store)  
Create an investor report for V_Metroway project using content from the PDFs. Write in a polished, professional style as the corporate communications director of İsra Holding.

## Content Requirements.

  1.	Identify major themes —
	•	If a PDF covers financial data, build a “Financial Overview” section.
	•	If it covers construction progress, create a “Construction Status” section.
	•	Continue the same logic for any other relevant topics.
	2.	Generate meaningful subsections under each theme, using clear headings that reflect the source material.
	3.	Insert supporting images only when the previous response already provided them and they genuinely illustrate the subsection.
	4.	Assemble the report in HTML following the established page structure (intro, divider, content pages). Each section belongs in its own content page, consistent with the design rules.

## 🎨 V_Metroway Design Requirements

### Required Files (use ONLY these exact names, no extensions or paths):
- `kapak_foto` - Blue section divider background
- `metroway_frame` - Pattern background  
- `isra_logo` - Company logo
- `metroway_foto` - Main project photo

## CRITICAL OUTPUT INSTRUCTION:
Return ONLY the HTML code starting from <!DOCTYPE html> and ending with </html>. 
DO NOT include any explanatory text, markdown formatting, or code blocks.
DO NOT include any text before <!DOCTYPE or after </html>.
Output ONLY pure HTML.

### Page Structure Requirements:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>V_Metroway Yatırımcı Raporu</title>
<style>
  /* Global Reset */
  body { margin: 0; padding: 0; }


  @page {
      size: A4;      
      margin: 0;     
    }
  
  .page {
    width: 210mm;
    height: 297mm;
    position: relative;
    overflow: hidden;
    page-break-after: always;
  }
  /* Full page background - MUST BE PRESENT */
  .bg-full {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: -1;
  }

  .corner-logo {
    position: absolute;
    right: 60px;
    bottom: 80px;
    height: 48px;
    opacity: .85;
    z-index: 10;
  }
  
  
  /* Intro Page Styles */
  .intro-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    position: relative;
  }
  
  /* Divider Page - CRITICAL STRUCTURE */
  .section-divider {
    position: relative;
   
  }
  
  /* Blue background - FULL A4 SIZE */
  .divider-bg-full {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  
  .divider-bg-full img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  

  .divider-title {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 25%;
    font: 700 42px/1 Arial, sans-serif;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #fff;
    text-align: center;
    text-shadow: 0 3px 10px rgba(0,0,0,.3);
    z-index: 1;
  }
  
  .content-page {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    /* padding kaldırıldı! */
    padding: 0;
    position: relative;
  }

  /* 2. İçerik kutusuna padding ver */
  .content-inner {
    max-width: 900px;
    width: 100%;
    /* padding’i buraya taşı */
    padding: 120px 40px;
    box-sizing: border-box; /* padding’in toplam genişliği bozmasın */
  }
    
  
  /* Text styles */
  .content-page h2 {
    font: 700 32px/1 Arial, sans-serif;
    color: #1B3A6B;
    margin-bottom: 25px;
  }
  
  .content-page p {
    font-size: 16px;
    line-height: 1.7;
    color: #444;
    margin-bottom: 20px;
    text-align: justify;  /* Better text distribution */
  }
  
  .content-page figure {
    margin: 30px auto;
    text-align: center;
    width: 100%;  /* Full width for figures */
  }
  
  .content-page figure img {
    max-width: 90%;  /* Slightly reduced to show it's contained */
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,.1);
    display: block;
    margin: 0 auto;
  }
  
  /* HIDE headers/footers on content and divider pages */
  .content-page header,
  .content-page footer,
  .section-divider header,
  .section-divider footer {
    display: none !important;
  }
</style>
</head>
<body>

<!-- Intro page structure -->
<section class="page intro-page">
  <header><img src="isra_logo" alt="İsra Logo" style="height:52px;margin-bottom:20px;"></header>
  <h1 style="font:700 38px/1 Arial,sans-serif;color:#1B3A6B;margin-bottom:20px;">V_Metroway Yatırımcı Raporu</h1>
  <p style="font-size:18px;color:#444;margin-bottom:30px;">1 Mart 2024 – 1 Mart 2025 Dönemi</p>
  <figure><img src="metroway_foto" alt="Proje" style="max-width:85%;border-radius:12px;box-shadow:0 2px 16px rgba(0,0,0,.1);"></figure>
  <footer style="position:absolute;bottom:30px;left:0;right:0;text-align:center;font-size:13px;color:#888;">
    <img src="isra_logo" style="height:48px;margin-bottom:10px;"><br>© 2025 İsra Holding.
  </footer>
</section>

<!-- Divider page - MUST have this exact structure -->
<section class="page section-divider">
  <div class="divider-bg-full">
    <img src="kapak_foto" alt="">
  </div>
  <h2 class="divider-title">(Based on the content generate new header/headers)</h2>
</section>

<!-- Content page - MUST have metroway_frame as first element -->
<section class="page content-page" >
  <img src="metroway_frame" alt="" class="bg-full">
  <div class="content-inner">
  <h2>Finansal Durum</h2>
  <p>{Content from PDFs will be filled here}</p>
  <figure>
    <img src="(example-photo-that was uploaded)" alt="Finansal Grafik">
  </figure>
  </div>
  <img src="isra_logo" alt="" class="corner-logo">
</section>

</body>
</html>
```

## STRICT RULES:

1. **OUTPUT FORMAT**: Return ONLY HTML code. No markdown, no explanations, no code blocks.
2. **DIVIDER PAGES**: MUST use divider-bg-full container with kapak_foto covering FULL A4 page
3. **CONTENT PAGES**: MUST have metroway_frame as the FIRST element with class="bg-full"
4. **NO HEADERS ON CONTENT PAGES**: Content pages must NOT have any header elements
5. **CORNER LOGO ONLY**: Content pages show ONLY the corner logo at bottom-right
6. **USE PROVIDED IMAGES**: Use exact image names without extensions
7. **CONTENT IMAGES**: When you receive image descriptions from the previous response, use those exact filenames in your HTML (e.g., if you see "finans-1750769809.webp - Financial chart showing...", use src="finans-1750769809.webp")
8. **FULL WIDTH CONTENT**: Ensure content uses the full page width with appropriate margins

## 🖼️ Content images
{{images_block}}

## IMPORTANT :
1. **One‐to-one mapping**
	•	Build exactly one section for each PDF provided.
	•	Name each section to match its PDF’s main topic (e.g., Financial Overview, Construction Status).
2. **Mandatory image placement**
	•	Use every uploaded image once.
	•	Place each image in the single section where it illustrates the content best (financial charts in the finance section, site photos in construction, etc.).

You MUST use these exact filenames in your HTML within figure tags:
```html
<figure>
  <img src="finans-1750.webp" alt="Financial chart">
</figure>
```

## FINAL INSTRUCTION:
Generate the complete HTML document following these rules. Start with <!DOCTYPE html> and end with </html>. Include nothing else.