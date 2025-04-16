from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
from pathlib import Path
import logging
from weasyprint import HTML, CSS, FontConfiguration
import tempfile

class ConvertHtmlToPdfTool(BaseTool):
    """
    HTML içeriğini WeasyPrint kullanarak PDF'e dönüştürür.
    WebContent Agent tarafından oluşturulan HTML'i alıp PDF dökümanı üretir.
    """
    
    project_name: str = Field(..., description="Proje adı")
    report_id: str = Field(..., description="Rapor ID")
    html_content: str = Field(..., description="PDF'e dönüştürülecek HTML içeriği")
    css_path: Optional[str] = Field(None, description="Opsiyonel CSS dosya yolu")
    
    def run(self) -> bytes:
        """
        Verilen HTML içeriğini PDF'e dönüştürür ve PDF bayt dizisini döndürür.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"[PDF_GEN] PDF oluşturma başlatıldı: Proje={self.project_name}")
        
        try:
            # Font yapılandırması
            font_config = FontConfiguration()
            
            # Temel CSS
            css_str = '@page { size: A4; margin: 1.5cm; @bottom-left { content: "İsra Holding"; font-size: 9pt; color: #666; } @bottom-right { content: "Sayfa " counter(page) " / " counter(pages); font-size: 9pt; color: #666; } }'
            stylesheets = [CSS(string=css_str, font_config=font_config)]
            
            # Eğer CSS dosyası belirtilmişse ekle
            if self.css_path and Path(self.css_path).is_file():
                stylesheets.append(CSS(filename=self.css_path, font_config=font_config))
                logger.info(f"[PDF_GEN] Harici CSS eklendi: {self.css_path}")
            
            # HTML oluştur ve PDF'e dönüştür
            html = HTML(string=self.html_content)
            pdf_bytes = html.write_pdf(stylesheets=stylesheets, font_config=font_config)
            
            logger.info(f"[PDF_GEN] PDF başarıyla oluşturuldu: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"[PDF_GEN] PDF oluşturma hatası: {str(e)}", exc_info=True)
            raise RuntimeError(f"PDF oluşturulurken hata: {str(e)}")