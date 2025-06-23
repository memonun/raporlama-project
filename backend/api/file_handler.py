import os
import json
import shutil
import logging
import time
from typing import Dict, List, Tuple, Any, Optional
import uuid
from pathlib import Path
from fastapi import UploadFile

# Logger setup 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define base paths
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
ACTIVE_REPORT_DIR = UPLOADS_DIR / "active_report"

def ensure_directory_structure(project_name: str) -> None:
    """
    Aktif rapor için gerekli dizin yapısını oluşturur.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    """
    project_dir = ACTIVE_REPORT_DIR / project_name.lower()
    images_dir = project_dir / "images"
    text_dir = project_dir / "text"
    
    # Ana dizinleri oluştur
    for dir_path in [project_dir, images_dir, text_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"[FILE] Dizin oluşturuldu: {dir_path}")

async def save_uploaded_image(project_name: str, component_name: str, 
                             image: UploadFile, image_index: int = 0, question_id: str = None) -> Tuple[bool, str, str]:
    """
    Bir bileşene ait görsel dosyasını kaydeder ve proje JSON'ında referansı günceller.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    component_name : str
        Bileşen adı
    image : UploadFile
        Yüklenen görsel dosyası
    image_index : int, optional
        Görsel indeksi (birden fazla görsel olabilir), default 0
    question_id : str, optional
        Soru ID'si (belirtilirse, JSON'da bu alana dosya referansı eklenir)
    
    Returns:
    --------
    Tuple[bool, str, str]
        (başarı durumu, dosya adı, hata mesajı)
    """
    try:
        # Proje için dizin yapısını kontrol et
        ensure_directory_structure(project_name)
        
        # Dosya adı standardizasyonu
        component_name_cleaned = component_name.lower().replace(" ", "_").replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ç", "c").replace("ö", "o")
        
        # Dosya uzantısını al
        file_ext = os.path.splitext(image.filename)[1].lower()
        
        # Yeni dosya adı: component_name-index.ext
        timestamp = int(time.time())
        new_filename = f"{component_name_cleaned}-{timestamp}{file_ext}"
        
        # Tam dosya yolu
        image_dir = ACTIVE_REPORT_DIR / project_name.lower() / "images"
        file_path = image_dir / new_filename
        relative_path = f"active_report/images/{project_name.lower()}/{new_filename}"
        
        # Dosyayı kaydet
        contents = await image.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"[FILE] Görsel kaydedildi: {file_path}")
        
        # Eğer question_id belirtildiyse, proje JSON'ında referansı güncelle
        if question_id:
            file_info = {
                "filename": image.filename,
                "path": relative_path,
                "type": "image"
            }
            
            add_file_entry_to_array(project_name, component_name, question_id, file_info)
        
        return True, new_filename, ""
    
    except Exception as e:
        logger.error(f"[FILE] Görsel kaydedilirken hata: {str(e)}", exc_info=True)
        return False, "", str(e)

def save_component_text(project_name: str, component_name: str, text_content: str) -> Tuple[bool, str]:
    """
    Bir bileşenin metin içeriğini kaydeder.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    component_name : str
        Bileşen adı
    text_content : str
        Kaydedilecek metin içeriği
    
    Returns:
    --------
    Tuple[bool, str]
        (başarı durumu, hata mesajı)
    """
    try:
        # Proje için dizin yapısını kontrol et
        ensure_directory_structure(project_name)
        
        # Bileşenler dosyası
        components_file = ACTIVE_REPORT_DIR / project_name.lower() / "text" / "components.json"
        
        # Dosya mevcut ise oku, değilse boş dict oluştur
        components_data = {}
        if components_file.exists():
            with open(components_file, "r", encoding="utf-8") as f:
                components_data = json.load(f)
        
        # Bileşen verisini ekle/güncelle
        components_data[component_name] = text_content
        
        # Dosyaya kaydet
        with open(components_file, "w", encoding="utf-8") as f:
            json.dump(components_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[FILE] Bileşen metni kaydedildi: {component_name} - {project_name}")
        
        return True, ""
    
    except Exception as e:
        logger.error(f"[FILE] Bileşen metni kaydedilirken hata: {str(e)}", exc_info=True)
        return False, str(e)

def get_active_report_images(project_name: str) -> List[str]:
    """
    Aktif rapor için yüklenen tüm görsellerin yollarını döndürür.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    
    Returns:
    --------
    List[str]
        Görsel dosya yollarının listesi
    """
    image_dir = ACTIVE_REPORT_DIR / project_name.lower() / "images"
    
    if not image_dir.exists():
        logger.warning(f"[FILE] Görsel dizini bulunamadı: {image_dir}")
        return []
    
    # Tüm görsel dosyaları bul
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')
    image_paths = [str(file) for file in image_dir.glob("*") 
                  if file.suffix.lower() in image_extensions]
    
    logger.info(f"[FILE] {len(image_paths)} adet görsel bulundu: {project_name}")
    
    return image_paths

def clean_active_report(project_name: str) -> bool:
    """
    Aktif rapor dosyalarını temizler (rapor sonlandırıldıktan sonra).
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    
    Returns:
    --------
    bool
        İşlem başarılı ise True, değilse False
    """
    project_dir = ACTIVE_REPORT_DIR / project_name.lower()
    
    if not project_dir.exists():
        logger.warning(f"[FILE] Temizlenecek aktif rapor dizini bulunamadı: {project_dir}")
        return True  # Zaten silinmiş olabilir
    
    try:
        # Dizini tamamen kaldır
        shutil.rmtree(project_dir)
        logger.info(f"[FILE] Aktif rapor dizini başarıyla temizlendi: {project_dir}")
        return True
    
    except Exception as e:
        logger.error(f"[FILE] Aktif rapor dizini temizlenirken hata: {str(e)}", exc_info=True)
        return False

def add_file_entry_to_array(project_name: str, component_name: str, question_id: str, file_info: Dict[str, Any]) -> bool:
    """
    Proje JSON dosyasındaki belirli bir alana dosya girişini bir diziye ekler.
    Eğer alan zaten bir dizi ise, dosyayı bu diziye ekler.
    Eğer alan tanımlı değilse veya dizi değilse, yeni bir dizi oluşturur ve dosyayı ekler.

    Parameters:
    -----------
    project_name : str
        Proje adı
    component_name : str
        Bileşen adı (JSON'daki üst seviye anahtar)
    question_id : str
        Soru ID'si (answers içindeki anahtar)
    file_info : Dict[str, Any]
        Dosya bilgisi (filename, path, type)

    Returns:
    --------
    bool
        İşlem başarılı ise True, değilse False
    """
    try:
        # Proje JSON dosyasını oku
        project_file_path = BASE_DIR / "data" / "projects" / f"{project_name}.json"
        
        # Dosya yoksa hata döndür
        if not project_file_path.exists():
            logger.error(f"[FILE] Proje dosyası bulunamadı: {project_file_path}")
            return False
            
        # JSON dosyasını oku
        with open(project_file_path, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        
        # Bileşen yoksa oluştur
        if component_name not in project_data:
            project_data[component_name] = {}
            
        # Answers yoksa oluştur
        if "answers" not in project_data[component_name]:
            project_data[component_name]["answers"] = {}
            
        # Soru ID'si yoksa veya dizi değilse, dizi oluştur
        if question_id not in project_data[component_name]["answers"] or not isinstance(project_data[component_name]["answers"][question_id], list):
            # Eğer mevcut bir değer varsa, onu dizinin ilk elemanı yap
            if question_id in project_data[component_name]["answers"] and project_data[component_name]["answers"][question_id]:
                existing_value = project_data[component_name]["answers"][question_id]
                project_data[component_name]["answers"][question_id] = [existing_value]
            else:
                project_data[component_name]["answers"][question_id] = []
                
        # Dosyayı diziye ekle
        project_data[component_name]["answers"][question_id].append(file_info)
        
        # JSON dosyasını güncelle
        with open(project_file_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"[FILE] Dosya referansı diziye eklendi: {file_info['filename']} -> {component_name}.answers.{question_id}")
        return True
        
    except Exception as e:
        logger.error(f"[FILE] Dosya referansı eklenirken hata: {str(e)}", exc_info=True)
        return False
