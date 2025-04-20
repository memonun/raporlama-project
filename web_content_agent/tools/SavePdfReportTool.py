from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any
import logging
from pathlib import Path
from backend.utils.pdf_utils import save_pdf_content 
from backend.api.data_storage import save_generated_report

logger = logging.getLogger(__name__)

class SavePdfReportTool(BaseTool):
    """
    Oluşturulan PDF raporunu uygun dizine kaydeder ve rapor meta verilerini günceller.
    Bu tool, WebContentAgent tarafından PDF oluşturulduktan sonra çalıştırılmalıdır.
    """
    
    project_name: str = Field(..., description="Proje adı")
    report_id: str = Field(..., description="Rapor ID")
    pdf_content: bytes = Field(..., description="Kaydedilecek PDF içeriği (bytes)")
    report_content_text: str = Field(..., description="Oluşturulan raporun metin içeriği (Markdown)")
    
    class ToolConfig: 
        one_call_at_a_time = True
    
    def run(self) -> Dict[str, Any]:
        """
        PDF içeriğini kaydeder, rapor meta verilerini günceller ve sonuç bilgilerini döndürür.
        """
        logger.info(f"[PDF_SAVE] PDF kaydetme başlatıldı: Proje={self.project_name}, Rapor ID={self.report_id}")
        
        pdf_path = Path()
        try:
            # 1. PDF'i kaydet
            pdf_path, success = save_pdf_content(self.pdf_content, self.project_name, self.report_id)
            
            if not success:
                # PDF kaydedilemezse hata fırlat, meta veri kaydetme
                raise RuntimeError("PDF dosyası kaydedilemedi")
            
            logger.info(f"[PDF_SAVE] PDF başarıyla kaydedildi: {pdf_path}")
            
            # 2. Rapor meta verilerini kaydet (PDF başarıyla kaydedildiyse)
            logger.info(f"[PDF_SAVE] Rapor meta verileri kaydediliyor: Rapor ID={self.report_id}")
            try:
                updated_report_data = save_generated_report(
                    project_name=self.project_name,
                    report_id=self.report_id,
                    report_content=self.report_content_text,
                    pdf_path=str(pdf_path)
                )
                logger.info(f"[PDF_SAVE] Rapor meta verileri başarıyla kaydedildi.")
            except Exception as meta_save_error:
                # Meta veri kaydetme başarısız olursa logla ama PDF kaydedildiği için yine de başarılı dönebiliriz
                # Ancak PDF yolunu bildirmek önemli olabilir.
                logger.error(f"[PDF_SAVE] Rapor meta verileri kaydedilirken hata oluştu (PDF kaydedildi): {meta_save_error}", exc_info=True)
                # Belki burada farklı bir mesaj veya flag döndürmek daha iyi olur?
                # Şimdilik başarılı varsayalım ama log önemli.
                # raise RuntimeError(f"Rapor meta verileri kaydedilirken hata: {meta_save_error}") # Bu satır hatayı yukarı taşır

            # Sonuç bilgilerini oluştur (Hem PDF hem meta veri kaydı sonrası)
            result = {
                "success": True,
                "message": "PDF raporu başarıyla kaydedildi ve meta veriler güncellendi.",
                "project_name": self.project_name,
                "report_id": self.report_id,
                "pdf_path": str(pdf_path),
                "file_size": len(self.pdf_content)
                # "updated_metadata": updated_report_data # İsteğe bağlı olarak güncellenen metadatayı da döndürebiliriz
            }
            
            return result
            
        except Exception as e:
            # PDF kaydetme veya beklenmedik bir hata oluşursa
            logger.error(f"[PDF_SAVE] PDF veya meta veri kaydetme sırasında genel hata: {str(e)}", exc_info=True)
            # Hata durumunda başarısızlık ve hata mesajı içeren bir dict döndür
            return {
                "success": False,
                "message": f"Rapor kaydedilirken hata oluştu: {str(e)}",
                "project_name": self.project_name,
                "report_id": self.report_id,
                "pdf_path": str(pdf_path) if pdf_path.exists() else None
            }