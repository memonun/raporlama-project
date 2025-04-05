"""
Bu modül, rapor verilerinin saklanması ve yönetilmesi için gerekli fonksiyonları içerir.
Her proje için tek bir aktif rapor tutulur.
"""

import os
import json
import datetime
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import shutil
import uuid

# Temel veri dizini
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
PROJECTS_DIR = DATA_DIR / "projects"

# Dizinleri kontrol et ve yoksa oluştur
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Arşiv dizinini de oluştur
ARCHIVE_DIR = PROJECTS_DIR / "archive"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Sabit proje listesi
DEFAULT_PROJECTS = ["V Mall", "V Metroway", "V Statü", "V Yeşilada"]

def initialize_projects():
    """
    Varsayılan projeleri oluşturur - eğer mevcut değilse
    """
    for project_name in DEFAULT_PROJECTS:
        project_path = get_project_path(project_name)
        if not project_path.exists():
            # Yeni proje verisi oluştur
            current_time = datetime.datetime.now().isoformat()
            project_data = {
                "project_name": project_name,
                "created_at": current_time,
                "last_updated": current_time,
                "active_report": None
            }
            
            # Verileri kaydet
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

def get_project_path(project_name: str) -> Path:
    """
    Proje adına göre proje veri dosyasının yolunu döndürür.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Proje veri dosyasının yolu
    """
    # Proje adındaki geçersiz karakterleri temizle
    safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name)
    return PROJECTS_DIR / f"{safe_name}.json"

def get_report_id(project_name: str) -> str:
    """
    Proje adı ve o anki tarih kullanılarak rapor ID'si oluşturur
    
    Args:
        project_name: Proje adı
        
    Returns:
        Rapor ID'si (format: {Projeadi}_{YYYYMMDD})
    """
    safe_project = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name)
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    return f"{safe_project}_{current_date}"

def create_new_report(project_name: str, report_id: str) -> Dict[str, Any]:
    """
    Bir proje için yeni bir rapor oluşturur.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID'si
        
    Returns:
        Oluşturulan rapor verileri
        
    Raises:
        ValueError: Eğer aynı report_id zaten varsa
    """
    project_path = get_project_path(project_name)
    
    # Proje verilerini yükle veya oluştur
    if not project_path.exists():
        project_data = {
            "project_name": project_name,
            "created_at": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat(),
            "active_report": None
        }
    else:
        with open(project_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
    
    # Eğer aktif bir rapor varsa hata fırlat
    if project_data.get("active_report"):
        raise ValueError(f"Aktif bir raporunuz bulunuyor. Lütfen mevcut raporu tamamlayın veya silin.")
    
    # Yeni rapor verisi oluştur
    current_time = datetime.datetime.now().isoformat()
    new_report = {
        "report_id": report_id,
        "report_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "created_at": current_time,
        "last_updated": current_time,
        "components": {},
        "status": "in_progress",
        "report_generated": False
    }
    
    # Aktif raporu güncelle
    project_data["active_report"] = new_report
    project_data["last_updated"] = current_time
    
    # Verileri kaydet
    with open(project_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    return new_report

def get_active_report(project_name: str) -> Optional[Dict[str, Any]]:
    """
    Projenin aktif raporunu getirir.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Aktif rapor verisi veya None
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        return None
    
    with open(project_path, 'r', encoding='utf-8') as f:
        project_data = json.load(f)
    
    # Yeni yapı: active_report
    if project_data.get("active_report"):
        return project_data.get("active_report")
    
    # Eski yapı: reports array
    if project_data.get("reports") and len(project_data["reports"]) > 0:
        # En son raporu döndür
        latest_report = project_data["reports"][0]
        
        # Eski yapıyı yeni yapıya dönüştür
        project_data["active_report"] = latest_report
        project_data.pop("reports", None)
        
        # Verileri kaydet
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        return latest_report
    
    return None

def save_component_data(project_name: str, component_name: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bir bileşen için verilen cevapları kaydeder.
    
    Args:
        project_name: Proje adı
        component_name: Bileşen adı
        answers: Cevaplar
        
    Returns:
        Güncellenmiş rapor verisi
        
    Raises:
        FileNotFoundError: Proje bulunamazsa
    """
    try:
        if not project_name:
            raise ValueError("Proje adı belirtilmedi")
        if not component_name:
            raise ValueError("Bileşen adı belirtilmedi")
            
        project_path = get_project_path(project_name)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Proje bulunamadı: {project_name}")
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON çözümleme hatası ({project_path}): {e}")
            raise ValueError(f"Proje dosyası bozulmuş olabilir: {str(e)}")
        
        active_report = project_data.get("active_report")
        if not active_report:
            # Aktif rapor bulunamadıysa, yeni bir rapor oluştur
            print(f"Proje {project_name} için aktif rapor bulunamadı, yeni rapor oluşturuluyor...")
            report_id = get_report_id(project_name)
            active_report = {
                "report_id": report_id,
                "report_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "components": {},
                "status": "in_progress",
                "report_generated": False
            }
            project_data["active_report"] = active_report
            print(f"Yeni rapor oluşturuldu: {report_id}")
        
        # Son güncelleme zamanını güncelle
        current_time = datetime.datetime.now().isoformat()
        project_data["last_updated"] = current_time
        active_report["last_updated"] = current_time
        
        # Bileşen verilerini güncelle
        if "components" not in active_report:
            active_report["components"] = {}
            
        # Cevapları güncellemeden önce mevcut veriyi logla
        existing_data = active_report["components"].get(component_name, {})
        print(f"Mevcut {component_name} verileri: {existing_data}")
        print(f"Yeni {component_name} cevapları: {answers}")
        
        # PDF içeriği için özel kontrol (RESTORED)
        if component_name == "pdf_content" and "content" in answers:
            # PDF içeriğini doğrudan active_report'a kaydet
            print("PDF içeriği algılandı, rapor verisine kaydediliyor...")
            content_length = len(answers["content"]) if answers["content"] else 0
            print(f"Kaydedilecek PDF içeriği uzunluğu: {content_length} karakter")
            active_report["pdf_content"] = answers["content"]
            
            # PDF dosya adını da kaydet
            if "filename" in answers:
                active_report["pdf_filename"] = answers["filename"]
                print(f"PDF dosya adı kaydedildi: '{answers['filename']}'")
                print(f"Aktif raporda pdf_filename anahtarı var mı: {'pdf_filename' in active_report}")
            else:
                print("PDF dosya adı bulunamadı, sadece içerik kaydedildi")
        else:
            # Normal bileşen cevaplarını kaydet
            active_report["components"][component_name] = {
                "answers": answers,
                "last_updated": current_time
            }
        
        # Verileri kaydet
        try:
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            print(f"{project_name} projesi {component_name} bileşeni verileri başarıyla kaydedildi.")
        except Exception as file_error:
            print(f"Dosya yazma hatası: {file_error}")
            raise IOError(f"Proje verisi kaydedilemedi: {str(file_error)}")
        
        return active_report
    except FileNotFoundError as e:
        # Proje bulunamadı hatası - bu hatayı üst katmana ilet
        print(f"Dosya bulunamadı hatası: {e}")
        raise e
    except json.JSONDecodeError as e:
        # JSON çözümleme hatası
        print(f"Proje dosyası JSON çözümleme hatası: {e}")
        raise ValueError(f"Proje dosyası bozulmuş olabilir: {str(e)}")
    except ValueError as e:
        # Değer hatası
        print(f"Değer hatası: {e}")
        raise e
    except IOError as e:
        # Dosya işlemi hatası
        print(f"Dosya işlemi hatası: {e}")
        raise e
    except Exception as e:
        # Genel hata
        print(f"Bileşen verileri kaydedilirken beklenmeyen hata: {e}")
        raise e

def delete_report(project_name: str) -> bool:
    """
    Projenin aktif raporunu siler.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Silme işlemi başarılı ise True
        
    Raises:
        FileNotFoundError: Proje bulunamazsa
        ValueError: Aktif rapor bulunamazsa
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        raise FileNotFoundError(f"Proje bulunamadı: {project_name}")
    
    with open(project_path, 'r', encoding='utf-8') as f:
        project_data = json.load(f)
    
    if not project_data.get("active_report"):
        raise ValueError("Aktif bir rapor bulunamadı")
    
    # Aktif raporu sil
    project_data["active_report"] = None
    project_data["last_updated"] = datetime.datetime.now().isoformat()
    
    # Verileri kaydet
    with open(project_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    return True

def get_all_projects() -> List[str]:
    """
    Tüm projeleri listeler.
    
    Returns:
        Proje adlarının listesi
    """
    projects = []
    for file in PROJECTS_DIR.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            projects.append(project_data["project_name"])
    return projects

def get_project_data(project_name: str) -> Optional[Dict[str, Any]]:
    """
    Proje verilerini getirir.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Proje verisi veya None
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        return None
    
    with open(project_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def archive_project(project_name: str) -> bool:
    """
    Projeyi arşivler.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Arşivleme işlemi başarılı ise True
        
    Raises:
        FileNotFoundError: Proje bulunamazsa
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        raise FileNotFoundError(f"Proje bulunamadı: {project_name}")
    
    # Arşiv dosyası oluştur
    archive_path = ARCHIVE_DIR / project_path.name
    shutil.move(str(project_path), str(archive_path))
    
    return True

def delete_project_data(project_name: str) -> bool:
    """
    Projeyi tamamen siler.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Silme işlemi başarılı ise True
        
    Raises:
        FileNotFoundError: Proje bulunamazsa
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        raise FileNotFoundError(f"Proje bulunamadı: {project_name}")
    
    os.remove(project_path)
    return True

def save_generated_report(project_name: str, report_id: str, report_content: str, pdf_path: str) -> Dict[str, Any]:
    """
    Oluşturulan raporun bilgilerini kaydeder.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID'si
        report_content: Oluşturulan rapor içeriği
        pdf_path: Oluşturulan PDF dosyasının yolu
        
    Returns:
        Güncellenmiş rapor verisi
        
    Raises:
        FileNotFoundError: Proje bulunamazsa
        ValueError: Aktif rapor bulunamazsa
    """
    project_path = get_project_path(project_name)
    
    if not project_path.exists():
        raise FileNotFoundError(f"Proje bulunamadı: {project_name}")
    
    with open(project_path, 'r', encoding='utf-8') as f:
        project_data = json.load(f)
    
    active_report = project_data.get("active_report")
    if not active_report:
        raise ValueError("Aktif bir rapor bulunamadı")
    
    # Rapor bilgilerini güncelle
    current_time = datetime.datetime.now().isoformat()
    project_data["last_updated"] = current_time
    active_report["last_updated"] = current_time
    active_report["report_content"] = report_content
    active_report["pdf_path"] = pdf_path
    active_report["report_generated"] = True
    active_report["status"] = "completed"
    
    # Verileri kaydet
    with open(project_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    return active_report

def finalize_report(project_name: str) -> Dict[str, Any]:
    """
    Raporu sonlandırır ve düzenlemeye kapatır.
    Sonlandırılan rapor vitrinde görüntülenir ve düzenlenemez.
    
    Args:
        project_name: Projenin adı
        
    Returns:
        Sonlandırılan rapor verisi
    """
    project_data = get_project_data(project_name)
    
    active_report = project_data.get("active_report")
    if not active_report:
        raise ValueError(f"{project_name} için aktif bir rapor bulunamadı")
    
    if not active_report.get("report_generated"):
        raise ValueError(f"Rapor henüz oluşturulmadı")
    
    # Raporu sonlandır
    active_report["is_finalized"] = True
    active_report["finalized_at"] = datetime.datetime.now().isoformat()
    
    # Projeyi kaydet
    with open(get_project_path(project_name), 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    return active_report

# Uygulamanın başlangıcında varsayılan projeleri oluştur (tüm fonksiyonlar tanımlandıktan sonra)
initialize_projects() 