import os
import logging
from typing import Optional
import tempfile
import pdfplumber

logger = logging.getLogger(__name__)

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    PDF dosyasından metin içeriğini çıkaracak fonksiyon (pdfplumber kullanarak)
    
    Args:
        filepath: PDF dosyasının yolu
        
    Returns:
        str: PDF'ten çıkarılan metin, hata durumunda None
    """
    try:
        # PDF dosyasını kontrol et
        if not os.path.exists(filepath):
            logger.error(f"PDF dosyası bulunamadı: {filepath}")
            return None
            
        # PDF'ten metin çıkar
        with pdfplumber.open(filepath) as pdf:
            text_content = ""
            
            # Tüm sayfalardan metin çıkar
            for page in pdf.pages:
                extracted_text = page.extract_text() or ""
                text_content += extracted_text + "\n"
                
            return text_content.strip()
    except Exception as e:
        logger.error(f"PDF işleme hatası: {str(e)}")
        return None 