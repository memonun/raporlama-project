import os
import logging
from typing import Optional, Tuple, List
from pathlib import Path
from datetime import datetime
import tempfile
import pdfplumber
import re
import shutil
import json
from uuid import uuid4
logger = logging.getLogger(__name__)

# Constants
BASE_REPORTS_DIR = Path("backend/data/reports")
BASE_ACTIVE_REPORT_DIR = Path("backend/data/uploads/active_report")
def get_active_report_id(project_name: str) -> str:
    """
    Proje adına göre aktif rapor ID'sini döndürür.
    
    Args:
        project_name: Proje adı
    """
    """
    Proje adına göre aktif rapor ID'sini döndürür.
    
    Args:
        project_name: Proje adı
        
    Returns:
        str: Aktif rapor ID'si veya None (aktif rapor yoksa)
    """
    try:
        # Proje dosyasının yolunu oluştur
        project_file = Path(f"data/projects/{project_name}.json")
        
        # Proje dosyasını oku
        if not project_file.exists():
            logger.warning(f"Proje dosyası bulunamadı: {project_file}")
            return None
            
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            
        # Active report kontrolü
        active_report = project_data.get('active_report')
        if not active_report:
            logger.info(f"Aktif rapor bulunamadı: {project_name}")
            return None
            
        report_id = active_report.get('report_id')
        if not report_id:
            logger.warning(f"Aktif raporda report_id bulunamadı: {project_name}")
            return None
            
        logger.info(f"Aktif rapor ID'si bulundu: {report_id}")
        return report_id
        
    except Exception as e:
        logger.error(f"Aktif rapor ID'si alınırken hata: {str(e)}", exc_info=True)
        return None

def create_report_id(project_name: str) -> str:
        """
        Proje adı ve UUID kullanılarak benzersiz rapor ID'si oluşturur
        
        Args:
            project_name: Proje adı
            
        Returns:
            Rapor ID'si (format: {Projeadi}_{UUID})
        """
        safe_project = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name)
        unique_id = str(uuid4())
        return f"{safe_project}_{unique_id}"


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

def ensure_active_report_structure(project_name: str) -> Path:
    """
    Aktif rapor işleme için gerekli dizin yapısını oluşturur ve proje yolunu döndürür.
    (backend/data/uploads/active_report/{proje_adı}/images ve text)

    Args:
        project_name: Proje adı

    Returns:
        Aktif rapor proje dizininin yolu (örn: backend/data/uploads/active_report/{proje_adı})
    """
    # Proje adını sanitize etmeye gerek yok, çünkü bu dizin adı API'den geliyor olabilir
    # ve orjinal haliyle kullanılması gerekebilir. Gerekirse burada da sanitize eklenebilir.
    project_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower()
    images_dir = project_dir / "images"
    text_dir = project_dir / "text"

    for dir_path in [project_dir, images_dir, text_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"[FILE] Aktif rapor dizini oluşturuldu: {dir_path}")
            
    return project_dir # Ana proje dizinini döndür

def clean_active_report_directory(project_name: str) -> bool:
    """
    Belirli bir proje için aktif rapor dizinini temizler (siler).
    
    Args:
        project_name: Temizlenecek proje adı
        
    Returns:
        bool: İşlem başarılıysa True, aksi halde False
    """
    try:
        project_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower()
        if not project_dir.exists():
            logger.warning(f"[CleanReport] Temizlenecek dizin bulunamadı: {project_dir}")
            return True # Dizin yoksa, zaten temizlenmiş sayılır
        
        shutil.rmtree(project_dir)
        logger.info(f"[CleanReport] Aktif rapor dizini temizlendi: {project_dir}")
        return True
    except Exception as e:
        logger.error(f"[CleanReport] Aktif rapor dizini temizlenirken hata: {str(e)}", exc_info=True)
        return False

def save_component_text(project_name: str, component_name: str, text_content: str) -> Tuple[bool, str]:
    """
    Bir projeye ait bileşenin metin içeriğini JSON dosyasına kaydeder.
    Dosya yoksa oluşturur, varsa günceller.

    Args:
        project_name: Proje adı
        component_name: Bileşen adı
        text_content: Kaydedilecek metin içeriği

    Returns:
        Tuple[bool, str]: (Başarı durumu, Hata mesajı (başarısızsa))
    """
    try:
        # Önce gerekli dizin yapısının var olduğundan emin ol
        project_dir = ensure_active_report_structure(project_name)
        components_file = project_dir / "text" / "components.json"
        
        components_data = {}
        # Eğer dosya varsa, mevcut içeriği oku
        if components_file.exists():
            try:
                with open(components_file, "r", encoding="utf-8") as f:
                    components_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"[SaveText] JSON dosyası okunamadı veya boş: {components_file}. Yeni dosya oluşturulacak.")
                # Hatalı veya boş dosyayı görmezden gel, üzerine yazılacak
                components_data = {}
            except Exception as read_err:
                logger.error(f"[SaveText] JSON okunurken beklenmedik hata: {components_file}, Hata: {read_err}", exc_info=True)
                return False, f"Mevcut JSON dosyası okunurken hata: {read_err}"

        # Yeni veriyi ekle veya güncelle
        components_data[component_name] = text_content
        
        # Güncellenmiş veriyi dosyaya yaz
        with open(components_file, "w", encoding="utf-8") as f:
            json.dump(components_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"[SaveText] Bileşen metni kaydedildi: {component_name} - Proje: {project_name}")
        return True, ""
        
    except Exception as e:
        logger.error(f"[SaveText] Bileşen metni kaydedilirken hata: {str(e)}", exc_info=True)
        return False, str(e)

def get_active_report_image_paths(project_name: str) -> List[str]:
    """
    Belirli bir projenin aktif rapor dizinindeki tüm görsellerin dosya yollarını döndürür.

    Args:
        project_name: Proje adı

    Returns:
        List[str]: Görsel dosyalarının string olarak yollarının listesi.
                   Dizin bulunamazsa veya hata olursa boş liste döner.
    """
    try:
        image_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower() / "images"
        if not image_dir.exists() or not image_dir.is_dir():
            logger.warning(f"[GetImages] Görsel dizini bulunamadı veya bir dizin değil: {image_dir}")
            return []

        # Yaygın görsel uzantıları
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff')

        image_paths = []
        for file in image_dir.glob("*"):
            # Dosya olduğundan ve geçerli bir uzantıya sahip olduğundan emin ol
            if file.is_file() and file.suffix.lower() in image_extensions:
                image_paths.append(str(file))

        logger.info(f"[GetImages] {len(image_paths)} adet görsel bulundu: Proje {project_name}")
        return image_paths

    except Exception as e:
        logger.error(f"[GetImages] Görseller alınırken hata: Proje {project_name}, Hata: {str(e)}", exc_info=True)
        return [] # Hata durumunda boş liste döndür

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