import os
import logging
from typing import Optional
import tempfile
import PyPDF2
import io

# PDF işleme için PyPDF2 kütüphanesi
try:
    from PyPDF2 import PdfReader
except ImportError:
    logging.warning("PyPDF2 kütüphanesi bulunamadı. 'pip install PyPDF2' komutu ile yükleyin.")

logger = logging.getLogger(__name__)

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    PDF dosyasından metin içeriğini çıkaracak fonksiyon
    
    Args:
        filepath: PDF dosyasının yolu
        
    Returns:
        str: PDF'ten çıkarılan metin, hata durumunda None
    """
    try:
        # PyPDF2 kütüphanesi kurulu mu kontrol et
        if 'PdfReader' not in globals():
            raise ImportError("PyPDF2 kütüphanesi kurulu değil.")
            
        # PDF dosyasını kontrol et
        if not os.path.exists(filepath):
            logger.error(f"PDF dosyası bulunamadı: {filepath}")
            return None
            
        # PDF'ten metin çıkar
        reader = PdfReader(filepath)
        text_content = ""
        
        # Tüm sayfalardan metin çıkar
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
            
        return text_content.strip()
    except Exception as e:
        logger.error(f"PDF işleme hatası: {str(e)}")
        return None 