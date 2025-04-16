from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import os
import base64
import logging

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProcessImagesForReportTool(BaseTool):
    """
    Resimleri rapor için işler ve base64 formatına dönüştürür.
    Bu araç, HTML raporlarında kullanılacak görselleri hazırlar.
    """
    
    project_name: str = Field(..., description="Proje adı")
    image_paths: List[str] = Field(..., description="İşlenecek görsel dosyalarının yolları")
    
    def run(self) -> List[Dict[str, str]]:
        """
        Verilen görsel yollarını işleyerek base64 formatına dönüştürür ve meta verilerle birlikte döndürür.
        """
        processed_images = []
        
        for image_path in self.image_paths:
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"[HTML_GEN] Görsel bulunamadı: {image_path}")
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
                logger.error(f"[HTML_GEN] Görsel işlenirken hata: {file_name} - {str(e)}")
                continue
        
        if not processed_images:
            logger.warning(f"[HTML_GEN] Hiçbir görsel işlenemedi. {len(self.image_paths)} görsel yolu verildi.")
        else:
            logger.info(f"[HTML_GEN] Toplam {len(processed_images)} görsel başarıyla işlendi.")
            
        return processed_images