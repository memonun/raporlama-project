## 🛠️ Tools available this turn
1. **file_search** – scoped to the vector-store IDs supplied in the API call.  

## 💼 Investor Report Template (from Vector Store)  
Create a summary text from the provided pdfs.
The pdf resources of information should be summarized and composed in a formal sense, creating an investor report with the provided sections and suitable headers (financials, construction states, any alerts) included in html. -->

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
7. Preserve the section order exactly; never invent new headers.  
8. Do **not** output JSON, Markdown, or explanations—**HTML only**.
9. The HTML must follow a formal, investor-relations tone (professional, data-driven, no colloquialisms).
10. Structure the body into the five sections listed in the Investor Report Template field below. Render each as a top-level <section> with an <h2> matching the template’s title.

11. Any figure, table, or claim must be backed by content returned via file_search; include inline citations immediately after the sentence that uses the data.

13. Never introduce new sections or deviate from the template headings—even if the PDFs mention other topics.
