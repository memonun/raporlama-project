import os
import logging
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
import tempfile
import pdfplumber
import re

logger = logging.getLogger(__name__)

# Constants
BASE_REPORTS_DIR = Path("data/reports")

def sanitize_filename(name: str) -> str:
    """
    Dosya adını güvenli hale getirir.
    
    Args:
        name: Orijinal isim
        
    Returns:
        Güvenli dosya adı
    """
    # Türkçe karakterleri ve boşlukları düzelt
    name = name.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    name = name.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    
    # Sadece alfanumerik karakterler, tire ve alt çizgi
    return re.sub(r'[^a-zA-Z0-9\-_]', '_', name)

def ensure_report_directory(project_name: str) -> Path:
    """
    Proje raporları için dizin oluşturur ve yolunu döndürür.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Proje rapor dizininin yolu
    """
    safe_project_name = sanitize_filename(project_name)
    project_dir = BASE_REPORTS_DIR / safe_project_name
    
    if not project_dir.exists():
        project_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Proje rapor dizini oluşturuldu: {project_dir}")
    
    return project_dir

def generate_report_filename(project_name: str, report_id: str) -> str:
    """
    Standart rapor dosya adı oluşturur.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Oluşturulan dosya adı
    """
    return f"{report_id}.pdf"

def get_report_path(project_name: str, report_id: str) -> Path:
    """
    Rapor dosyasının tam yolunu oluşturur.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Rapor dosyasının tam yolu
    """
    project_dir = ensure_report_directory(project_name)
    filename = generate_report_filename(project_name, report_id)
    return project_dir / filename

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    PDF dosyasından metin içeriğini çıkarır.
    
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

def save_pdf_content(content: bytes, project_name: str, report_id: str) -> Tuple[Path, bool]:
    """
    PDF içeriğini dosyaya kaydeder.
    
    Args:
        content: PDF içeriği (bytes)
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Tuple[Path, bool]: (Dosya yolu, başarı durumu)
    """
    try:
        pdf_path = get_report_path(project_name, report_id)
        
        # PDF içeriğini kaydet
        with open(pdf_path, 'wb') as f:
            f.write(content)
            
        logger.info(f"PDF başarıyla kaydedildi: {pdf_path}")
        return pdf_path, True
        
    except Exception as e:
        logger.error(f"PDF kaydedilirken hata: {str(e)}")
        return Path(), False

def get_pdf_info(pdf_path: Path) -> Optional[dict]:
    """
    PDF dosyası hakkında temel bilgileri döndürür.
    
    Args:
        pdf_path: PDF dosyasının yolu
        
    Returns:
        dict: PDF bilgileri veya None
    """
    try:
        if not pdf_path.exists():
            logger.error(f"PDF dosyası bulunamadı: {pdf_path}")
            return None
            
        file_size = pdf_path.stat().st_size
        created_time = datetime.fromtimestamp(pdf_path.stat().st_ctime)
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
        return {
            "file_path": str(pdf_path),
            "file_size": file_size,
            "created_at": created_time.isoformat(),
            "page_count": page_count
        }
        
    except Exception as e:
        logger.error(f"PDF bilgileri alınırken hata: {str(e)}")
        return None 