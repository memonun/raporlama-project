from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import os
import base64
import logging
from pathlib import Path
from backend.api.file_handler import get_active_report_images, ACTIVE_REPORT_DIR

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProcessImagesForReportTool(BaseTool):
    """
    Resimleri rapor için işler ve base64 formatına dönüştürür.
    Bu araç, HTML raporlarında kullanılacak görselleri hazırlar.
    """
    
    project_name: str = Field(..., description="Proje adı")
    image_paths: List[str] = Field(None, description="İşlenecek görsel dosyalarının yolları (opsiyonel)")
    
    class ToolConfig:
        one_call_at_a_time = True
    
    def run(self) -> List[Dict[str, str]]:
        """
        Verilen görsel yollarını işleyerek base64 formatına dönüştürür ve meta verilerle birlikte döndürür.
        Eğer hiç görsel işlenemezse ValueError fırlatır.
        """
        processed_images = []
        initial_image_count = 0
        
        # Eğer image_paths verilmemişse, aktif rapor dizininden al
        if not self.image_paths:
            self.image_paths = get_active_report_images(self.project_name)
            logger.info(f"[HTML_GEN] Aktif rapor dizininden {len(self.image_paths)} görsel alındı")
        
        initial_image_count = len(self.image_paths) if self.image_paths else 0
        
        if not self.image_paths:
            logger.warning(f"[HTML_GEN] İşlenecek görsel yolu bulunamadı (Proje: {self.project_name})")
            self.image_paths = [] # Ensure it's an empty list if None
            
        for image_path in self.image_paths:
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"[HTML_GEN] Görsel bulunamadı veya geçersiz yol: {image_path}")
                continue
            
            # Dosya adı ve uzantısını al
            file_name = os.path.basename(image_path)
            _, file_ext = os.path.splitext(file_name)
            file_ext = file_ext.lower()
            
            # MIME tipi belirle
            mime_type = None
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif file_ext == '.png':
                mime_type = 'image/png'
            elif file_ext == '.svg':
                mime_type = 'image/svg+xml'
            elif file_ext == '.gif':
                mime_type = 'image/gif'
            else:
                logger.warning(f"[HTML_GEN] Desteklenmeyen görsel formatı: {file_ext} ({file_name}). Varsayılan olarak image/jpeg kullanılacak.")
                mime_type = 'image/jpeg'  # Varsayılan
            
            try:
                # Görsel datası
                with open(image_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                # Base64 URL oluştur
                data_url = f"data:{mime_type};base64,{img_data}"
                
                # Bazı meta verilerle birlikte ekle
                processed_images.append({
                    'src': data_url,
                    'name': file_name,
                    'type': mime_type,
                    'alt': f"{self.project_name} - {file_name}"
                })
                
                logger.info(f"[HTML_GEN] Görsel işlendi: {file_name}")
                
            except Exception as e:
                logger.error(f"[HTML_GEN] Görsel işlenirken hata: {file_name} - {str(e)}", exc_info=True)
                continue
        
        processed_count = len(processed_images)
        
        if processed_count == 0 and initial_image_count > 0:
            logger.error(f"[HTML_GEN] Başlangıçta {initial_image_count} görsel vardı ancak hiçbiri başarıyla işlenemedi.")
            raise ValueError(f"[HTML_GEN] Sağlanan {initial_image_count} görselden hiçbiri işlenemedi. Lütfen dosya yollarını, formatlarını ve izinleri kontrol edin.")
        elif processed_count == 0 and initial_image_count == 0:
             logger.warning(f"[HTML_GEN] İşlenecek hiç görsel bulunamadı veya sağlanmadı (Proje: {self.project_name}).")
             # Return empty list if no images were provided initially
             return []
        else:
            logger.info(f"[HTML_GEN] Toplam {processed_count}/{initial_image_count} görsel başarıyla işlendi.")
            
        return processed_images