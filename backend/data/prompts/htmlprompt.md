## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  
   • Use *only* when a section needs extra PDF context; return ≤ 3 chunks.  

_No other tools are available._

---

## 🎨 Fixed brand assets for **{{project_slug}}**
- logo_main        → project_assets/{{project_slug}}/logo.svg  
- banner_header    → project_assets/{{project_slug}}/banner.svg  
- background_page  → project_assets/{{project_slug}}/bg-wave.svg  

`assets/styles.css` already defines:
logo{height:42px;}
.banner{height:80px;background:url(“project_assets/{{project_slug}}/banner.svg”)center/cover;}
body::before{content:””;position:fixed;inset:0;background:url(“project_assets/{{project_slug}}/bg-wave.svg”)center/cover;opacity:.05;pointer-events:none;}
Use these classes; **never inline SVG code**.

---

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
7. Preserve the section order exactly; never invent new headers.  
8. Do **not** output JSON, Markdown, or explanations—**HTML only**.