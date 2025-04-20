from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, List, Any, Optional
import json
import logging

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GenerateDynamicHtmlTool(BaseTool):
    """
    Komponentler, stiller ve görselleri kullanarak dinamik HTML raporu oluşturur.
    Bu araç, raporun son HTML çıktısını üretir ve WeasyPrint ile PDF dönüşümüne hazırlar.
    """
    
    project_name: str = Field(..., description="Proje adı")
    report_text: str = Field(..., description="Investor Report Agent tarafından oluşturulan rapor metni")
    style_config: Dict[str, Any] = Field(..., description="Proje stil yapılandırması,get_project_style_config_tool tarafından alınır")
    image_urls: List[Dict[str, str]] = Field(..., description="İşlenmiş görseller listesi, direkt files folderından alınabilir.")
    svg_backgrounds: Dict[str, str] = Field({}, description="SVG arkaplan görsellerinin data URI'leri")
    
    class ToolConfig:
        one_call_at_a_time = True
    
    def run(self) -> str:
        """
        Verilen rapor metni, stil ve görsel verilerini kullanarak estetik bir HTML raporu oluşturur.
        Çıktı WeasyPrint ile PDF dönüşümüne uygun olmalıdır.
        """
        logger.info(f"[HTML_GEN] Dinamik HTML oluşturma başlatıldı: Proje={self.project_name}")
        
        # Tüm görselleri log'a yazdır
        for img in self.image_urls:
            logger.info(f"[HTML_GEN] Kullanılabilir görsel: {img['name']}")
        
        # SVG arkaplanlarını log'a yazdır
        for key, value in self.svg_backgrounds.items():
            if value:
                logger.info(f"[HTML_GEN] SVG arkaplan mevcut: {key}")
        
        # HTML şablonunu oluştur
        html_content = self._create_html_template()
        
        # SVG arkaplan görsellerini HTML içine yerleştir
        html_content = self._insert_svg_backgrounds(html_content)
        
        # Görsel URL'lerini ekle
        html_content = self._insert_image_urls(html_content)
        
        logger.info(f"[HTML_GEN] HTML içeriği başarıyla oluşturuldu: {len(html_content)} karakter")
        return html_content
    
    def _create_html_template(self) -> str:
        """HTML şablonunu oluşturur."""
        # Proje renkleri
        colors = self.style_config.get('colors', {})
        primary_color = colors.get('primary', '#3366CC')
        secondary_color = colors.get('secondary', '#6699FF')
        accent_color = colors.get('accent', '#FF9900')
        background_color = colors.get('background', '#F5F7FA')
        text_color = colors.get('text', '#333333')
        
        # Font bilgisi
        font = self.style_config.get('font', 'Arial, sans-serif')
        
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - Yatırımcı Raporu</title>
    <style>
        :root {{
            --primary-color: {primary_color};
            --secondary-color: {secondary_color};
            --accent-color: {accent_color};
            --background-color: {background_color};
            --text-color: {text_color};
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: {font}, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 0;
        }}
        
        .container {{
            max-width: 210mm; /* A4 genişliği */
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background-color: var(--primary-color);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }}
        
        .header h1 {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        
        section {{
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        h2 {{
            color: var(--primary-color);
            margin-bottom: 15px;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 5px;
        }}
        
        h3 {{
            color: var(--secondary-color);
            margin: 15px 0 10px;
        }}
        
        p {{
            margin-bottom: 10px;
        }}
        
        ul, ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        figure {{
            margin: 20px 0;
            text-align: center;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        figcaption {{
            font-style: italic;
            color: #666;
            margin-top: 5px;
            font-size: 14px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        table, th, td {{
            border: 1px solid #ddd;
        }}
        
        th {{
            background-color: var(--primary-color);
            color: white;
            padding: 10px;
            text-align: left;
        }}
        
        td {{
            padding: 10px;
        }}
        
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background-color: var(--primary-color);
            color: white;
            border-radius: 8px;
        }}
        
        @media print {{
            body {{
                background-color: white;
            }}
            
            .container {{
                max-width: 100%;
                padding: 0;
            }}
            
            section, .header, .footer {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{self.project_name} - Yatırımcı Raporu</h1>
        </header>
        
        <main>
            {self.report_text}
        </main>
        
        <footer class="footer">
            <p>© {self.project_name} {self._get_current_year()} | Tüm Hakları Saklıdır</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def _insert_svg_backgrounds(self, html_content: str) -> str:
        """SVG arkaplan görsellerini HTML içine yerleştirir."""
        # Logo yerleştirme
        logo_uri = self.svg_backgrounds.get('logo', '')
        if logo_uri:
            logo_html = f'<img id="logo" src="{logo_uri}" alt="{self.project_name} Logo" style="max-height: 80px; margin-bottom: 15px;">'
            html_content = html_content.replace('<h1>', f'{logo_html}<h1>')
        
        # Kapak arkaplanı yerleştirme
        cover_bg_uri = self.svg_backgrounds.get('cover_bg', '')
        if cover_bg_uri:
            html_content = html_content.replace(
                '.header {', 
                f'.header {{ background-image: url("{cover_bg_uri}"); background-size: cover; background-position: center;'
            )
        
        # Genel arkaplan yerleştirme
        general_bg_uri = self.svg_backgrounds.get('general_bg', '')
        if general_bg_uri:
            html_content = html_content.replace(
                'body {', 
                f'body {{ background-image: url("{general_bg_uri}"); background-size: cover; background-attachment: fixed;'
            )
        
        return html_content
    
    def _insert_image_urls(self, html_content: str) -> str:
        """Görsel URL'lerini HTML içerisindeki placeholder'lar ile değiştirir."""
        for img in self.image_urls:
            img_name = img['name']
            img_src = img['src']
            img_alt = img.get('alt', img_name)
            
            # Placeholder pattern: [IMAGE:image_name]
            placeholder = f'[IMAGE:{img_name}]'
            img_html = f'<figure><img src="{img_src}" alt="{img_alt}"><figcaption>{img_name}</figcaption></figure>'
            
            html_content = html_content.replace(placeholder, img_html)
        
        return html_content
    
    def _get_current_year(self) -> str:
        """Şu anki yılı döndürür."""
        from datetime import datetime
        return str(datetime.now().year)