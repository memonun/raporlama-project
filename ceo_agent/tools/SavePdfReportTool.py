from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any
import logging
from pathlib import Path
from backend.utils.pdf_utils import save_pdf_content, get_report_path 
class SavePdfReportTool(BaseTool):
    """
    Oluşturulan PDF raporunu uygun dizine kaydeder ve rapor meta verilerini günceller.
    Bu tool, WebContentAgent tarafından PDF oluşturulduktan sonra çalıştırılmalıdır.
    """
    
    project_name: str = Field(..., description="Proje adı")
    report_id: str = Field(..., description="Rapor ID")
    pdf_content: bytes = Field(..., description="Kaydedilecek PDF içeriği (bytes)")
    
    class ToolConfig:
        one_call_at_a_time = True
    
    def run(self) -> Dict[str, Any]:
        """
        PDF içeriğini kaydeder ve sonuç bilgilerini döndürür.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"[PDF_SAVE] PDF kaydetme başlatıldı: Proje={self.project_name}, Rapor ID={self.report_id}")
        
        try:
            # PDF'i kaydet
            pdf_path, success = save_pdf_content(self.pdf_content, self.project_name, self.report_id)
            
            if not success:
                raise RuntimeError("PDF dosyası kaydedilemedi")
            
            # Sonuç bilgilerini oluştur
            result = {
                "success": True,
                "message": "PDF raporu başarıyla kaydedildi",
                "project_name": self.project_name,
                "report_id": self.report_id,
                "pdf_path": str(pdf_path),
                "file_size": len(self.pdf_content)
            }
            
            logger.info(f"[PDF_SAVE] PDF başarıyla kaydedildi: {pdf_path}")
            return result
            
        except Exception as e:
            logger.error(f"[PDF_SAVE] PDF kaydetme hatası: {str(e)}", exc_info=True)
            raise RuntimeError(f"PDF kaydedilirken hata: {str(e)}")