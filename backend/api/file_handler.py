import os
from api.data_storage import get_project_path
import json
import shutil
import logging
import time
import datetime
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
    pdf_dir = project_dir / "pdfs"
    
    # Ana dizinleri oluştur
    for dir_path in [project_dir, images_dir,pdf_dir]:
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
        relative_path = f"active_report/{project_name.lower()}/images/{new_filename}"
        
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

async def save_uploaded_pdf(project_name: str, component_name: str, file: UploadFile, question_id: str) -> Tuple[bool, str, str]:
    """Save a PDF under active_report/<project>/pdfs and update project JSON via add_file_entry_to_array."""
    try:
        ensure_directory_structure(project_name)  # creates .../pdfs as part of ensure_directory_structure

        # Sanitize and build filename
        file_ext = os.path.splitext(file.filename)[1].lower() or '.pdf'
        timestamp = int(time.time())
        safe_component = component_name.lower().replace(' ', '_')
        new_filename = f"{safe_component}-{timestamp}{file_ext}"

        pdf_dir = ACTIVE_REPORT_DIR / project_name.lower() / 'pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        file_path = pdf_dir / new_filename
        relative_path = f"active_report/{project_name.lower()}/pdfs/{new_filename}"

        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)

        file_info = {
            'filename': file.filename,
            'path': relative_path,
            'type': 'pdf'
        }
        add_file_entry_to_array(project_name, component_name, question_id, file_info)
        return True, new_filename, ''
    except Exception as e:
        logger.error(f'[FILE] PDF save error: {str(e)}', exc_info=True)
        return False, '', str(e)

    
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

def add_file_entry_to_array(
    project_name: str,
    component_name: str,
    question_id: str,
    file_info: Dict[str, str]
) -> bool:
    """Always maintains files as arrays and adds an upload timestamp."""
    try:
        project_path = get_project_path(project_name)

        if not project_path.exists():
            logger.error(f"[FILE] Project file not found: {project_path}")
            return False

        with open(project_path, "r+", encoding="utf-8") as f:
            data = json.load(f)

            # Ensure active_report and components structure exists
            report = data.setdefault("active_report", {})
            components = report.setdefault("components", {})
            component = components.setdefault(component_name, {"answers": {}})
            answers = component.setdefault("answers", {})

            # Always keep the answer under question_id as a list
            existing = answers.get(question_id)
            if existing is None:
                answers[question_id] = []
            elif not isinstance(existing, list):
                # Wrap single entry into a list, or reset if it's falsy
                answers[question_id] = [existing] if existing else []

            # Add timestamp
            file_info = dict(file_info)  # copy to avoid mutating input
            file_info["uploaded_at"] = datetime.datetime.now().isoformat()

            # Check for duplicates by path
            if any(
                isinstance(entry, dict) and entry.get("path") == file_info.get("path")
                for entry in answers[question_id]
            ):
                logger.info(f"File already present: {file_info.get('path')}")
                return True

            # Append and write back
            answers[question_id].append(file_info)
            logger.info(f"File added: {file_info.get('path')}")

            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

        return True

    except (IOError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error updating project JSON: {e}", exc_info=True)
        return False

def remove_file_entry_from_array(
    project_name: str,
    component_name: str,
    question_id: str,
    file_to_remove: Dict[str, str]
) -> bool:
    """Proje JSON'undaki bir sorudan dosya referansını kaldırır."""
    try:
        from api.data_storage import get_project_path
        project_path = get_project_path(project_name)

        if not project_path.exists():
            logger.error(f"[FILE] Proje dosyası bulunamadı: {project_path}")
            return False

        with open(project_path, "r+", encoding="utf-8") as f:
            data = json.load(f)

            if "active_report" not in data or "components" not in data["active_report"]:
                logger.warning("Kaldırılacak dosya için aktif rapor veya bileşenler bulunamadı.")
                return False

            components = data["active_report"]["components"]

            if (component_name not in components or
                    "answers" not in components[component_name] or
                    question_id not in components[component_name]["answers"]):
                logger.warning("Kaldırılacak dosya için bileşen veya soru bulunamadı.")
                return False

            file_list = components[component_name]["answers"][question_id]

            if not isinstance(file_list, list):
                logger.warning(f"'{question_id}' için dosya listesi bir liste değil.")
                return False

            path_to_remove = file_to_remove.get("path")
            if not path_to_remove:
                logger.error("Kaldırılacak dosya için 'path' belirtilmedi.")
                return False

            initial_count = len(file_list)
            new_file_list = [
                file_entry for file_entry in file_list
                if not (isinstance(file_entry, dict) and file_entry.get("path") == path_to_remove)
            ]

            if len(new_file_list) == initial_count:
                logger.warning(f"Dosya listede bulunamadı: {path_to_remove}")
                return False

            components[component_name]["answers"][question_id] = new_file_list
            logger.info(f"Dosya kaldırıldı: {path_to_remove}")

            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

        return True
    except (IOError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Proje JSON güncellenirken hata: {e}", exc_info=True)
        return False
