from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any
import logging
import json
from pathlib import Path
from api.data_storage import save_generated_report, get_project_path

class UpdateReportStatusTool(BaseTool):
    """
    Rapor durumunu "oluşturuldu" olarak günceller ve meta verileri kaydeder.
    PDF oluşturup kaydettikten sonra, raporun durumunu güncellemek için kullanılır.
    """
    
    project_name: str = Field(..., description="Proje adı")
    report_id: str = Field(..., description="Rapor ID")
    report_content: str = Field(..., description="Rapor metin içeriği")
    pdf_path: str = Field(..., description="Kaydedilen PDF'in dosya yolu")
    
    def run(self) -> Dict[str, Any]:
        """
        Rapor durumunu günceller ve sonuç bilgilerini döndürür.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"[REPORT_STATUS] Rapor durumu güncelleniyor: Proje={self.project_name}, Rapor ID={self.report_id}")
        
        try:
            # Rapor meta verilerini güncelle
            result = save_generated_report(
                self.project_name,
                self.report_id,
                self.report_content,
                self.pdf_path
            )
            
            logger.info(f"[REPORT_STATUS] Rapor durumu başarıyla güncellendi")
            return {
                "success": True,
                "message": "Rapor durumu başarıyla güncellendi",
                "project_name": self.project_name,
                "report_id": self.report_id,
                "report_data": result
            }
            
        except Exception as e:
            logger.error(f"[REPORT_STATUS] Rapor durumu güncellenirken hata: {str(e)}", exc_info=True)
            raise RuntimeError(f"Rapor durumu güncellenirken hata: {str(e)}")