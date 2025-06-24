from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi.responses import FileResponse
import os
from pathlib import Path
import smtplib
from api.mail_agent import send_missing_info_request, get_department_email, send_report_email as mail_agent_send_report
from api.questions_handler import get_questions_for_component
from api.data_storage import (
    save_component_data, get_project_data, get_all_projects, 
    save_generated_report, delete_project_data, archive_project, 
    create_new_report, delete_report as delete_report_from_storage,
    finalize_report, get_project_path,
    reset_active_report_generation
)

from api.file_handler import save_uploaded_image, save_uploaded_pdf, clean_active_report, add_file_entry_to_array, remove_file_entry_from_array
from fastapi.staticfiles import StaticFiles
import json
import datetime
import tempfile
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from openai import OpenAI
import base64
import logging
import sys
import time
from werkzeug.utils import secure_filename
from flask import jsonify, request, send_file  # <-- Add this import

from utils.pdf_utils import (
    extract_text_from_pdf,
    get_pdf_info,
    
)

from utils.pdf_utils import (
    get_report_path,
    create_report_id,
    get_active_report_id,
    save_pdf_content,
)

from models.basemodels import (
    ProjectRequest, ComponentDataRequest, EmailRequest,
   DeleteProjectRequest,ArchiveProjectRequest, 
   GenerateReportRequest, ShareReportRequest, DeleteFinalizedReportRequest
)

project_root = Path(__file__).resolve().parent.parent

template_dir = Path(__file__).parent / 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

# Statik dosya yolu (görseller için)
STATIC_DIR = Path(__file__).parent / 'static'
IMAGES_DIR = STATIC_DIR / 'images'

# Proje kök dizinini sys.path listesine ekle (eğer zaten yoksa)
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)



app = FastAPI(title="Yatırımcı Raporu API")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için. Prodüksiyonda spesifik origin belirtin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



# Endpoints
@app.get("/")
async def root():
    return {"message": "Yatırımcı Raporu API'ye Hoş Geldiniz"}

@app.get("/projects", response_model=List[str])
def get_projects():
    """Tüm projeleri getirir."""
    try:
        return get_all_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Projeler getirilirken bir hata oluştu: {str(e)}")

@app.get("/projects/default", response_model=List[str])
def get_default_projects():
    """Varsayılan projeleri getirir."""
    try:
        return get_all_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Varsayılan projeler getirilirken bir hata oluştu: {str(e)}")

@app.get("/project/{project_name}", response_model=Dict[str, Any])
def get_project_details(project_name: str):
    """Belirli bir projenin detaylarını getirir."""
    try:
        project_data = get_project_data(project_name)
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
            
        # Eğer active_report varsa ve finalized ise, reports listesine taşı
        active_report = project_data.get("active_report")
        if active_report and active_report.get("is_finalized"):
            # Reports listesi yoksa oluştur
            if "reports" not in project_data:
                project_data["reports"] = []
                
            # Finalized raporu listeye ekle
            project_data["reports"].insert(0, active_report)
            
            # Active report'u temizle
            project_data["active_report"] = None
            
            # Değişiklikleri kaydet
            try:
                with open(get_project_path(project_name), 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)
                print(f"Finalized rapor {active_report.get('report_id')} active_report'tan reports listesine taşındı ve dosya güncellendi.")
            except IOError as e:
                print(f"HATA: Düzeltilmiş proje verisi ({project_name}) dosyaya kaydedilemedi: {str(e)}")
                # Hata durumunda ne yapılacağına karar verilebilir. Şimdilik sadece logluyoruz.
                # İsteğe bağlı olarak hatayı yeniden yükseltebilir veya farklı bir yanıt dönebiliriz.
        
        return project_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proje detayları getirilirken bir hata oluştu: {str(e)}")

@app.get("/project/{project_name}/report/active", response_model=Optional[Dict[str, Any]])
def get_active_report(project_name: str):
    """Belirli bir projenin aktif raporunu getirir."""
    try:
        project_data = get_project_data(project_name)
        active_report = project_data.get("active_report")
        if not active_report:
            # 404 yerine null dönüşü ile frontend'in kontrol etmesine izin veriyoruz
            return None
            
        return active_report
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aktif rapor getirilirken bir hata oluştu: {str(e)}")

@app.post("/project/create-report", response_model=Dict[str, Any])
def create_report(request: ProjectRequest):
    """Yeni bir rapor oluşturur."""
    try:
        report_id = create_report_id(request.project_name)
        print(f"Report ID: {report_id}")
        report_data = create_new_report(
            request.project_name,
            report_id
        )
        return report_data
    except ValueError as e:
        if "zaten aktif bir rapor var" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulurken bir hata oluştu: {str(e)}")

@app.get("/components", response_model=List[str])
def get_components():
    """Tüm bileşenleri getirir."""
    try:
        return ["İşletme", "Finans", "İnşaat", "Kurumsal İletişim"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bileşenler getirilirken bir hata oluştu: {str(e)}")

@app.get("/component/{component_name}/questions")
def get_component_questions(component_name: str):
    """Belirli bir bileşenin sorularını getirir."""
    try:
        questions = get_questions_for_component(component_name)
        if not questions:
            raise HTTPException(status_code=404, detail=f"{component_name} için sorular bulunamadı")
        # Dict içinde questions array döndür
        return {"questions": questions}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Bileşen bulunamadı: {component_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bileşen soruları getirilirken bir hata oluştu: {str(e)}")

@app.post("/component/save-data", response_model=Dict[str, Any])
def save_component_data_endpoint(request: ComponentDataRequest):
    """Bir bileşen için cevapları kaydeder."""
    try:
        if not request.project_name:
            raise HTTPException(status_code=400, detail="Proje adı belirtilmedi")
        if not request.component_name:
            raise HTTPException(status_code=400, detail="Bileşen adı belirtilmedi")
        
        # İlk olarak projenin varlığını kontrol et
        try:
            project_data = get_project_data(request.project_name)
            if not project_data:
                raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
        
        # Cevapları doğrula
        if not isinstance(request.answers, dict):
            raise HTTPException(status_code=400, detail="Cevaplar bir sözlük (dictionary) formatında olmalıdır")
        
        # Bileşen verilerini kaydet
        try:
            result = save_component_data(
                request.project_name,
                request.component_name,
                request.answers
            )
            return result
        except ValueError as e:
            # Değer hatası
            print(f"Değer hatası: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError as e:
            # Dosya bulunamadı hatası
            print(f"Dosya bulunamadı hatası: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except IOError as e:
            # Dosya işlemi hatası
            print(f"IO hatası: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Dosya işlemi hatası: {str(e)}")
        except Exception as e:
            # Diğer hatalar
            print(f"Bileşen verisi kaydedilirken beklenmeyen hata: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Bileşen verisi kaydedilirken beklenmeyen hata: {str(e)}")
    except FileNotFoundError as e:
        # Proje veya dosya bulunamadı
        print(f"Dosya bulunamadı hatası: {str(e)}")
        if "Proje bulunamadı" in str(e):
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        # Veri doğrulama hatası
        print(f"Değer hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Zaten HTTP hatası ise doğrudan yükselt
        raise e
    except Exception as e:
        # Genel hata
        import traceback
        traceback.print_exc()
        print(f"Bileşen verileri kaydedilirken beklenmeyen hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bileşen verileri kaydedilirken bir hata oluştu: {str(e)}")

@app.post("/project/{project_name}/upload-component-image", response_model=Dict[str, Any])
async def upload_component_image(
    project_name: str,
    component_name: str = Form(...),
    question_id: str = Form(...),
    image_index: int = Form(0),
    image: UploadFile = File(...)
):
    """
    Bir bileşene ait görsel yükler.
    Görsel, aktif rapor klasörüne kaydedilir ve bileşen bazlı dosya adıyla saklanır.
    Görsel referansını proje JSON dosyasındaki dosya dizisine ekler.
    """
    logger.info(f"[IMAGE] Görsel yükleme isteği alındı: Proje={project_name}, Bileşen={component_name}, Soru={question_id}")
    
    try:
        # Görsel türünü kontrol et
        if not image.content_type or not image.content_type.startswith(("image/", "application/")):
            logger.error(f"[IMAGE] Geçersiz dosya türü: {image.content_type}")
            raise HTTPException(status_code=400, detail="Sadece resim dosyaları yüklenebilir")
        
        # Görsel dosyasını kaydet
        success, filename, error_msg = await save_uploaded_image(
            project_name, 
            component_name, 
            image,
            image_index,
            question_id  # Soru ID'sini geçiyoruz
        )
        
        if not success:
            logger.error(f"[IMAGE] Görsel kaydedilirken hata: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Görsel kaydedilemedi: {error_msg}")
            
        logger.info(f"[IMAGE] Görsel başarıyla kaydedildi: {filename}")
        
        # Güncel dosya dizisini al
        project_file_path = get_project_path(project_name)
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            
        # Güncel dosya dizisini al (Doğru yoldan)
        file_array = []
        active_report = project_data.get("active_report", {})
        if active_report:
            components = active_report.get("components", {})
            component_data = components.get(component_name, {})
            answers = component_data.get("answers", {})
            file_array = answers.get(question_id, [])
        
        # Başarı durumunda bilgi döndür
        return {
            "success": True,
            "message": "Görsel başarıyla yüklendi",
            "file_name": filename,
            "component": component_name,
            "files": file_array  # Güncel dosya dizisini dön
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[IMAGE] Görsel yükleme hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Görsel yükleme sırasında beklenmeyen hata: {str(e)}")




@app.get("/download-report/{project_name}")
def download_report(project_name: str):
    """Oluşturulan raporu indirir."""
    try:
        # Proje verisini al
        project_data = get_project_data(project_name)
        active_report = project_data.get("active_report")
        
        if not active_report:
            raise ValueError("Aktif bir rapor bulunamadı")
            
        if not active_report.get("report_generated"):
            raise ValueError("Rapor henüz oluşturulmamış")
            
        # Get report_id from the active report
        report_id = active_report.get("report_id")
        if not report_id:
            raise ValueError("Aktif raporda report_id bulunamadı")

        # Generate the path using the utility function
        pdf_path_obj = get_report_path(project_name, report_id)
        pdf_path = str(pdf_path_obj) # Convert to string for os.path.exists and FileResponse

        if not os.path.exists(pdf_path):
            logger.error(f"PDF dosyası bulunamadı (indirilirken): {pdf_path}")
            raise FileNotFoundError(f"PDF dosyası sunucuda bulunamadı: {pdf_path}")
            
        return FileResponse(
            path=pdf_path,
            filename=f"{project_name}_report.pdf",
            media_type="application/pdf"
        )
    except FileNotFoundError as e:
        # Log the error for debugging
        print(f"PDF Dosyası Bulunamadı: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        # Log the error for debugging
        print(f"Değer Hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the unexpected error
        import traceback
        traceback.print_exc()
        print(f"Beklenmeyen hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rapor indirilirken bir hata oluştu: {str(e)}")



@app.delete("/project/{project_name}/delete-report", response_model=Dict[str, Any])
def delete_project_report_endpoint(project_name: str):
    """Bir projenin aktif raporunu siler."""
    try:
        # Call the correctly imported function from data_storage
        result = delete_report_from_storage(project_name)
        if result: # delete_report_from_storage returns True on success
            print(f"Aktif rapor silindi: {project_name}")
            return {"message": "Aktif rapor başarıyla silindi", "project_name": project_name}
        else:
             # This case might not be reachable if delete_report_from_storage raises errors
             # but included for completeness based on boolean return type.
             raise HTTPException(status_code=500, detail="Rapor silme fonksiyonu False döndürdü.")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
    except ValueError as e:
        # Catch specific errors from delete_report_from_storage if it raises them
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected error during deletion
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Rapor silinirken beklenmeyen bir hata oluştu: {str(e)}")


@app.post("/project/delete", response_model=Dict[str, str])
def delete_project(request: DeleteProjectRequest):
    """Bir projeyi siler."""
    try:
        delete_project_data(request.project_name)
        return {"message": f"{request.project_name} projesi başarıyla silindi"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proje silinirken bir hata oluştu: {str(e)}")



@app.post("/project/archive", response_model=Dict[str, Any])
def archive_project(request: ArchiveProjectRequest):
    """Bir projeyi arşivler."""
    try:
        return archive_project(request.project_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proje arşivlenirken bir hata oluştu: {str(e)}")

@app.post("/send-email")
def send_email(request: EmailRequest):
    """Eksik bilgiler için talep e-postası gönderir."""
    try:
        # Bileşene göre departman e-postasını al
        to_email = get_department_email(request.component_name)
        
        result = send_missing_info_request(to_email, request.project_name, request.component_name)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"E-posta gönderilirken bir hata oluştu: {str(e)}")

@app.post("/project/finalize-report", response_model=Dict[str, Any])
def finalize_project_report(request: ProjectRequest):
    """Bir raporu sonlandırır ve vitrinde kilitli olarak işaretler."""
    try:
        # Proje verisini al
        project_data = get_project_data(request.project_name)
        if not project_data.get("active_report"):
            raise ValueError("Aktif bir rapor bulunamadı")
            
        # Raporu sonlandır
        result = finalize_report(request.project_name)
        
        # Geçici dosyaları temizle
        cleaned = clean_active_report(request.project_name)
        if not cleaned:
            logger.warning(f"[FINALIZE] Aktif rapor dosyaları temizlenemedi: {request.project_name}")
        
        return {"success": True, "message": "Rapor başarıyla sonlandırıldı", "report_data": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor sonlandırılırken hata oluştu: {str(e)}")

# @app.get("/project/{project_name}/unfinalized-reports")
# def get_unfinalized_reports(project_name: str):
#     """Bir projeye ait tamamlanmamış raporları getirir."""
#     try:
#         # Projeye ait raporları al
#         reports = get_project_reports(project_name)
        
#         # Tamamlanmamış raporları filtrele
#         unfinalized_reports = [report for report in reports if report.get("is_finalized") == False]
        
#         return {"reports": unfinalized_reports}
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Tamamlanmamış raporlar getirilirken bir hata oluştu: {str(e)}")

@app.get("/project/{project_name}/report/{report_id}/download")
def download_specific_report(project_name: str, report_id: str):
    """Belirli bir ID'ye sahip raporun PDF'ini indirir."""
    try:
        project_data = get_project_data(project_name)
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")

        target_report = None
        
        # Önce aktif raporda ara
        active_report = project_data.get("active_report")
        if active_report and active_report.get("report_id") == report_id:
            target_report = active_report
        
        # Aktif raporda bulunamazsa, geçmiş raporlarda ara
        if not target_report:
            for report in project_data.get("reports", []):
                if report.get("report_id") == report_id:
                    target_report = report
                    break
        
        # Rapor bulunamadıysa
        if not target_report:
            raise HTTPException(status_code=404, detail=f"Belirtilen ID ({report_id}) ile rapor bulunamadı")
        
        # PDF oluşturulmuş mu kontrol et
        if not target_report.get("report_generated"):
            raise HTTPException(status_code=400, detail="Rapor henüz PDF olarak oluşturulmamış")
            
        # PDF yolunu al ve kontrol et
        pdf_path = get_report_path(project_name, report_id)
        if not pdf_path.exists():
            logger.error(f"PDF dosyası bulunamadı: {pdf_path}")
            raise HTTPException(status_code=404, detail="Raporun PDF dosyası sunucuda bulunamadı")
            
        # PDF bilgilerini al
        pdf_info = get_pdf_info(pdf_path)
        if not pdf_info:
            raise HTTPException(status_code=500, detail="PDF dosyası okunamadı")
            
        # Dosyayı döndür
        filename = f"{project_name}_{report_id}_report.pdf"
        return FileResponse(
            path=str(pdf_path),
            filename=filename,
            media_type="application/pdf"
        )

    except FileNotFoundError: # Bu get_project_data'dan gelebilir
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
    except HTTPException as e: # Kendi HTTP hatalarımızı tekrar yükselt
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc() # Genel hataları logla
        raise HTTPException(status_code=500, detail=f"Rapor indirilirken beklenmeyen bir hata oluştu: {str(e)}")

# Statik dosyalar için (oluşturulan PDF'leri indirmek için)
app.mount("/download", StaticFiles(directory="./"), name="download")



@app.post("/project/delete-finalized-report", response_model=Dict[str, Any])
def delete_finalized_report(request: DeleteFinalizedReportRequest):
    """Bir projenin sonlandırılmış raporlarından birini siler."""
    logger.info(f"[MAIN] Finalized rapor silme isteği alındı: Proje={request.project_name}, Dosya/ID={request.file_name}")
    try:
        project_name = request.project_name
        file_name_or_id = request.file_name # This could be name or report_id
        
        # Proje kontrolü
        project_data = get_project_data(project_name)
        if not project_data:
            logger.warning(f"[MAIN] Finalized rapor silme: Proje bulunamadı - {project_name}")
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
        
        # Finalized rapor listesini kontrol et
        finalized_reports = project_data.get("reports", [])
        
        # Verilen dosya adıyla veya ID ile eşleşen finalized raporu bul
        found_report_index = -1
        found_report = None
        for i, report in enumerate(finalized_reports):
            # Check if the report is finalized and matches the provided name or ID
            if report.get("is_finalized") and (
                report.get("name") == file_name_or_id or 
                report.get("report_id") == file_name_or_id
            ):
                found_report = report
                found_report_index = i
                break
        
        if not found_report:
            logger.warning(f"[MAIN] Finalized rapor silme: Rapor bulunamadı - Proje={project_name}, Dosya/ID={file_name_or_id}")
            raise HTTPException(status_code=404, detail=f"Belirtilen finalized rapor bulunamadı: {file_name_or_id}")
        
        report_id = found_report.get("report_id")
        if not report_id:
            # This shouldn't happen for generated reports, but good to check
            logger.error(f"[MAIN] Finalized rapor silme: Rapor ID bulunamadı! Rapor Verisi: {found_report}")
            raise HTTPException(status_code=500, detail=f"Raporun ID bilgisi eksik, silinemiyor.")

        # PDF dosyasını ve finalized raporu sil
        try:
            # Generate the expected PDF path using the report_id
            logger.info(f"[MAIN] Finalized rapor PDF siliniyor: Proje={project_name}, Rapor ID={report_id}")
            pdf_path_obj = get_report_path(project_name, report_id)
            pdf_path = str(pdf_path_obj)

            # Attempt to delete the PDF file
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    logger.info(f"[MAIN] Finalized PDF dosyası başarıyla silindi: {pdf_path}")
                except OSError as e:
                    # Log error but proceed with metadata removal
                    logger.error(f"[MAIN] Finalized PDF dosyası ({pdf_path}) silinirken OS hatası: {str(e)}", exc_info=True)
            else:
                logger.warning(f"[MAIN] Silinecek finalized PDF dosyası bulunamadı (zaten yok): {pdf_path}")
            
            # Finalized raporu proje verilerinden kaldır (using the found index)
            logger.info(f"[MAIN] Finalized rapor meta verisi kaldırılıyor: Proje={project_name}, Rapor ID={report_id}")
            del project_data["reports"][found_report_index]
            project_data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Güncellenmiş proje verilerini kaydet (use r+ mode for safe update)
            project_json_path = get_project_path(project_name)
            with open(project_json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[MAIN] Finalized rapor başarıyla silindi: Proje={project_name}, Rapor ID={report_id}")
            return {
                "message": "Finalized rapor başarıyla silindi", 
                "project_name": project_name,
                "file_name": file_name_or_id # Return the identifier used in request
            }
        except Exception as e:
            logger.error(f"[MAIN] Finalized rapor silme işlemi sırasında iç hata: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Finalized rapor silinirken bir hata oluştu: {str(e)}")
        
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finalized rapor silinirken bir hata oluştu: {str(e)}")

@app.post("/extract-pdf")
async def extract_pdf_endpoint(file: UploadFile = File(...)):
    """
    PDF dosyasından içerik çıkarır ve metin olarak döndürür.
    """
    # Dosya türü kontrolü
    if not file.content_type or "application/pdf" not in file.content_type:
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları işlenebilir")
    
    try:
        # Geçici dosya oluştur ve PDF'i kaydet
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        try:
            contents = await file.read()
            temp_file.write(contents)
            temp_file.close()
            
            # PDF içeriğini çıkar
            extracted_content = extract_text_from_pdf(temp_file.name)
            if extracted_content is None:
                raise HTTPException(status_code=500, detail="PDF içeriği çıkarılamadı")
            
            # İçeriği JSON olarak döndür
            return {"content": extracted_content}
        finally:
            # Geçici dosyayı temizle
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"Geçici dosya silinirken hata: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF işleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF işlenirken hata oluştu: {str(e)}")




# Renk paletini getir
# def get_project_colors(project_name):
#     return PROJECT_PALETTES.get(project_name.lower(), {})

# Görsel yolunu veya base64 verisini getir
def get_image_path_or_data(project_name: str, image_filename: Optional[str] = None) -> Optional[str]:
    """Projeye ait görselin yolunu veya base64 kodlu verisini döndürür."""
    if not image_filename:
        # Varsayılan bir görsel veya logo döndürülebilir
        default_logo_path = IMAGES_DIR / 'isra_logo.png' # Varsayılan logo yolu
        if default_logo_path.is_file():
            return default_logo_path.as_uri()
        return None

    # Projeye özel görsel
    project_image_path = IMAGES_DIR / project_name.lower() / image_filename
    if project_image_path.is_file():
        # return project_image_path.as_uri() # Dosya yolu olarak döndür
        # Alternatif: Base64 olarak döndür (HTML içine gömmek için)
        try:
            with open(project_image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            # MIME türünü belirle (dosya uzantısına göre)
            ext = project_image_path.suffix.lower()
            mime_type = f'image/{ext[1:]}' if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg'] else 'image/png'
            return f'data:{mime_type};base64,{image_data}'
        except Exception as e:
            print(f"Hata: Görsel base64'e çevrilemedi ({project_image_path}): {e}")
            return None # Hata durumunda None döndür
            
    print(f"Uyarı: Görsel bulunamadı: {project_image_path}")
    return None

@app.post("/project/{project_name}/report/{report_id}/send-email")
async def send_report_email(project_name: str, report_id: str, email_request: ShareReportRequest):
    """Send a report to specified email addresses."""
    logger.info(f"[MAIN] Email report request received: Project={project_name}, ReportID={report_id}")
    try:
        result = mail_agent_send_report(project_name, report_id, email_request.email_addresses)
        logger.info(f"[MAIN] Email report successful: Project={project_name}, ReportID={report_id}")
        return result
    except FileNotFoundError as e:
        logger.warning(f"[MAIN] Email report failed: PDF not found - {str(e)}")
        raise HTTPException(status_code=404, detail="Report PDF file not found and cannot be sent.")
    except Exception as e:
        # Log the detailed error from mail_agent or other issues
        logger.error(f"[MAIN] Email report failed: Project={project_name}, ReportID={report_id}, Error: {str(e)}", exc_info=True)
        # Return a generic 500 error but check the logs for specifics
        detail_message = str(e) if isinstance(e, smtplib.SMTPAuthenticationError) else "Failed to send report email due to an internal error."
        raise HTTPException(status_code=500, detail=detail_message)

@app.post("/project/{project_name}/reset-active-report")
def reset_active_report_endpoint(project_name: str):
    """
    Endpoint to reset the active report generation status and delete the PDF.
    """
    logger.info(f"[API] Received request to reset active report for project: {project_name}")
    try:
        logger.info(f"[API] Calling data_storage.reset_active_report_generation for {project_name}")
        updated_report = reset_active_report_generation(project_name)
        
        if updated_report is None:
            # This case should ideally not happen if the button is only shown when there *is* an active report,
            # but we handle it defensively.
            logger.warning(f"[API] Reset was called, but no active report was found by data_storage for {project_name}. Returning 404.")
            raise HTTPException(status_code=404, detail="Sıfırlanacak aktif rapor bulunamadı.")
        
        logger.info(f"[API] Active report for {project_name} reset successfully. Returning updated report data.")
        return {"message": "Aktif rapor başarıyla sıfırlandı.", "active_report": updated_report}
        
    except FileNotFoundError as e:
        logger.error(f"[API] Reset failed for {project_name}: Project data file not found. Detail: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e)) # Project file not found
    except ValueError as e:
        logger.error(f"[API] Reset failed for {project_name}: Value error (e.g., missing report_id). Detail: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) # E.g., Missing report ID
    except IOError as e:
        logger.error(f"[API] Reset failed for {project_name}: IO error accessing project data. Detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Proje verisi okunurken/yazılırken hata: {str(e)}") # File system error
    except Exception as e:
        logger.error(f"[API] Reset failed for {project_name}: Unexpected error. Detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Aktif rapor sıfırlanırken beklenmeyen bir hata oluştu: {str(e)}")


# @app.post("/project/generate-report-by-agency")
# async def generate_report_by_agency(request: GenerateReportRequest):
#     """
#     Agency Swarm kullanarak asenkron olarak rapor oluşturur, kaydeder ve sonucu döndürür.
#     """
#     try:
#         logger.info(f"[AGENCY_REPORT_GEN] Rapor oluşturma başlatıldı. Proje={request.project_name}")

#         # --- 1. Veri Hazırlama --- 
#         messages = []
#         for comp_name, comp in request.components_data.items():
#             if "answers" in comp:
#                 for question_id, answer in comp["answers"].items():
#                     try:
#                         # Cevap JSON formatında mı diye kontrol et (örn. PDF içeriği)
#                         data = json.loads(answer)
#                         if isinstance(data, dict):
#                             content = data.get('content', '')
#                             file_name = data.get('fileName', 'Unnamed')
#                             messages.append(f"{comp_name} - {file_name}:\n{content}")
#                         else:
#                             messages.append(f"{comp_name} - Question {question_id}:\n{answer}")
#                     except json.JSONDecodeError:
#                         # If answer is not JSON, use it directly
#                         messages.append(f"{comp_name} - Question {question_id}:\n{answer}")

#         components_data = str("\n\n".join(messages))

#         # Combine project assets and image attachments
#         project_assets = load_project_shared_files(request.project_name)

#         # pdf_paths = get_project_pdf_paths(request.project_name)
#         # pdf_attachments = get_pdf_attachments(pdf_paths)

#         image_paths = get_project_image_paths(request.project_name)
#         image_attachments = get_image_attachments(image_paths)

#         # combined_attachments = image_attachments + pdf_attachments
       
#         # Agency prompt'unu hazırla
#         prompt = f"""
#                 Bu görev için ilgili proje adı: {request.project_name}.
#         Kullanıcı, bu görev için bazı görseller yükledi. Bu görseller, raporda uygun yerlerde kullanılmalıdır. 

#         Görseller arasında finansal tablolar, işletme fotoğrafları veya proje logoları olabilir. Aşağıdaki kurallara dikkat et:

#         1. Her görseli en uygun bölümde yerleştir.
#         2. Görselleri codeinterpreter kullanarakbase64 formatında ve tam olarak <img src="data:image/png;base64,..."> şeklinde oluştur.
#         3. Her base64 görsel verisi geçerli ve tamamen yüklenmiş olmalıdır.
#         4. MIME türü doğru eşleşmelidir (örneğin: image/png veya image/jpeg).
#         5. Yarım veya kesik base64 verisi göndermemelisin. WeasyPrint ile hatasız işlenebilir olmalıdır.
#         6. Görsel adı genellikle içeriği açıklar. Adlara dikkat et ve hangi bölümde kullanılabileceğini tahmin et.
#         7. Görsel açıklaması gerekiyorsa, uygun bir başlık veya altyazı kullan.

#         Raporu HTML formatında oluştur, stil ve düzen açısından şık bir yapı kullan. Gerekiyorsa <section> ve <figure> etiketlerinden faydalan.
#                 """
#         style_config = json.dumps(get_style_config(request.project_name))
#         # Get response from agency
#         # result = agency.get_completion_parse(
#         #     message=f"Oluşturulacak raporun ait oudğu proje: project_name: {request.project_name}, bütün bileşen içerikleri: {components_data}, stil yapılandırması: {style_config}",
#         #     additional_instructions=prompt,
#         #     response_format=MyHTMLResponse,
#         #     attachments=image_attachments
#         # )
        
       
#         logger.info(f"[AGENCY_REPORT_GEN] HTML response received. Proje={request.project_name}")

#         # Check if the agency returned an error message or HTML
#         # A simple check: valid HTML usually starts with <!DOCTYPE or <html>
#         if not isinstance(result.content, str) or not result.content.strip().lower().startswith(("<!doctype", "<html")):
#             logger.error(f"[AGENCY_REPORT_GEN] Agency returned an error or invalid content: {result}")
#             # Assuming the result string IS the error message based on updated CEO instructions
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Agency failed to generate HTML content: {result}"
#             )
        
#         logger.info(f"[AGENCY_REPORT_GEN] Agency returned valid HTML content. Proceeding with PDF generation.")
#         # Generate PDF from agency response (HTML content is in 'result')

#         print(f"Agency response: {result.content}")
#         pdf_result = await generate_pdf_from_agency_response(request.project_name, result.content)
        
#         if pdf_result.status == "error":
#             raise HTTPException(
#                 status_code=500,
#                 detail=pdf_result.message
#             )

#         return {
#             "status": "success",
#             "message": "Rapor başarıyla oluşturuldu",
#             "report_content": result,
#             "report_id": pdf_result.report_id,
#             "pdf_path": pdf_result.pdf_path
#         }

#     except Exception as e:
#         logger.error(f"[AGENCY_REPORT_GEN] Rapor oluşturma hatası: Proje={request.project_name}, Hata: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Agency ile rapor oluşturulurken bir hata oluştu: {str(e)}"
#         )
# async def generate_pdf_from_agency_response(project_name: str, agency_response: str) -> AgencyFinalResponse:
#     """
#     Takes the agency's response and generates a PDF using WeasyPrint.
    
#     Args:
#         project_name: Name of the project
#         agency_response: HTML/text content from the agency
        
#     Returns:
#         AgencyFinalResponse object containing status and file details
#     """
#     try:
#         logger.info(f"[PDF_GEN] Starting PDF generation for project: {project_name}")
        
#         # Get report ID 
#         report_id = get_active_report_id(project_name)
#         logger.info(f"[PDF_GEN] Generated report ID: {report_id}")
        
#         # Create basic HTML structure
#         html_content = agency_response
#         # Configure WeasyPrint
#         font_config = FontConfiguration()
#         css = CSS(string='', font_config=font_config)
        
#         # Generate PDF
#         html = HTML(string=html_content)
#         pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)
#         logger.info(f"[PDF_GEN] PDF generated successfully, size: {len(pdf_bytes)} bytes")
        
#         # Save PDF
#         pdf_path, success = save_pdf_content(pdf_bytes, project_name, report_id)
#         if not success:
#             raise ValueError("Failed to save PDF file")
#         logger.info(f"[PDF_GEN] PDF saved successfully at: {pdf_path}")
        
#         # Update project metadata
#         save_generated_report(
#             project_name,
#             report_id,
#             agency_response,  # Store the original content
#             str(pdf_path)
#         )
#         logger.info(f"[PDF_GEN] Project metadata updated successfully")
        
#         return AgencyFinalResponse(
#             status="success",
#             message="PDF report successfully generated and saved",
#             report_id=report_id,
#             pdf_path=str(pdf_path)
#         )
        
#     except Exception as e:
#         logger.error(f"[PDF_GEN] Error generating PDF: {str(e)}", exc_info=True)
#         return AgencyFinalResponse(
#             status="error",
#             message=f"Failed to generate PDF: {str(e)}",
#             report_id=None,
#             pdf_path=None
#         )

# Backend route for PDF deletion
@app.delete('/api/project/{project_name}/delete-pdf')
async def delete_pdf(project_name: str, path: str):
    """
    Yüklenen PDF dosyasını siler ve JSON referansını kaldırır.
    """
    if not path:
        raise HTTPException(status_code=400, detail="Dosya yolu belirtilmedi")
    
    # Construct the absolute path to the PDF file
    base_path = '/Users/memico/Documents/ISRA/Raporlama_otomasyonu/backend/data/uploads'
    full_path = os.path.join(base_path, path)
    
    # Security check to prevent path traversal attacks
    if not os.path.normpath(full_path).startswith(base_path):
        raise HTTPException(status_code=403, detail="Geçersiz dosya yolu")
    
    try:
        # Delete the file if it exists
        if os.path.exists(full_path):
            os.remove(full_path)
            
        # Update database reference to remove the PDF (assuming this function exists)
        # TODO: Update this to use proper array handling for multi-file support
        # remove_pdf_reference(project_name, path)
        
        return {"success": True, "message": "PDF başarıyla silindi"}
    except Exception as e:
        logger.error(f"[PDF] PDF silme hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF silinirken beklenmeyen hata: {str(e)}")

# Backend route for PDF upload
@app.post('/project/{project_name}/upload-pdf')
async def upload_pdf(project_name: str, file: UploadFile = File(...), component: str = Form(...), question_id: str = Form(...)):
    """
    Bir bileşene ait PDF dosyasını yükler.
    PDF dosyası, proje klasörüne kaydedilir ve referansı JSON'a eklenir.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Dosya yok")
    
    if not file.filename or not component or not question_id:
        raise HTTPException(status_code=400, detail="Eksik parametre")
    
    try:
        # Save uploaded PDF using the new helper function
        success, filename, error_msg = await save_uploaded_pdf(project_name, component, file, question_id)
        
        if not success:
            logger.error(f"[PDF] PDF kaydedilirken hata: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PDF kaydedilemedi: {error_msg}")
        
        logger.info(f"[PDF] PDF başarıyla kaydedildi: {filename}")
        
        # Güncel dosya dizisini al
        project_file_path = get_project_path(project_name)
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            
        # Get the current file array from the project data (Doğru yoldan)
        file_array = []
        active_report = project_data.get("active_report", {})
        if active_report:
            components = active_report.get("components", {})
            component_data = components.get(component, {})
            answers = component_data.get("answers", {})
            file_array = answers.get(question_id, [])
        
        return {
            'success': True,
            'fileName': filename,  # Return the filename from save_uploaded_pdf
            'filePath': f"active_report/{project_name.lower()}/pdfs/{filename}", # Path based on our convention
            'files': file_array  # Return the updated file array
        }
    except Exception as e:
        logger.error(f"[PDF] PDF yükleme hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF yükleme sırasında beklenmeyen hata: {str(e)}")

# Backend route for PDF viewing
@app.get('/api/project/{project_name}/view-pdf')
async def view_pdf(project_name: str, path: str):
    """
    PDF dosyasını görüntüler.
    """
    if not path:
        raise HTTPException(status_code=400, detail="Dosya yolu belirtilmedi")
    
    # Construct the absolute path to the PDF file
    base_path = '/Users/memico/Documents/ISRA/Raporlama_otomasyonu/backend/data/uploads'
    full_path = os.path.join(base_path, path)
    
    # Security check to prevent path traversal attacks
    if not os.path.normpath(full_path).startswith(base_path):
        raise HTTPException(status_code=403, detail="Geçersiz dosya yolu")
    
    try:
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="PDF dosyası bulunamadı")
        return FileResponse(path=full_path, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF] PDF görüntüleme hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF görüntülenirken beklenmeyen hata: {str(e)}")

# PDF storage functions are now handled by file_handler.py through save_uploaded_pdf and ensure_directory_structure

def remove_pdf_reference(project_name: str, file_path: str) -> bool:
    """
    Proje JSON dosyasından PDF referansını kaldırır.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    file_path : str
        Silinecek dosyanın yolu
    
    Returns:
    --------
    bool
        İşlem başarılı ise True, değilse False
    """
    try:
        project_file_path = os.path.join('/Users/memico/Documents/ISRA/Raporlama_otomasyonu/backend/data/projects', f"{project_name}.json")
        
        # Dosya yoksa hata döndür
        if not os.path.exists(project_file_path):
            logger.error(f"[FILE] Proje dosyası bulunamadı: {project_file_path}")
            return False
        
        # JSON dosyasını oku
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Değiştirdik mi?
        changed = False
        
        # Tüm bileşenleri kontrol et
        for component_name, component_data in project_data.items():
            if isinstance(component_data, dict) and "answers" in component_data:
                answers = component_data["answers"]
                
                # Tüm soruları kontrol et
                for question_id, files in answers.items():
                    # Eğer files bir liste değilse, atla
                    if not isinstance(files, list):
                        continue
                    
                    # Dosya yolu eşleşen elemanı bul ve kaldır
                    for i, file_info in enumerate(files):
                        if isinstance(file_info, dict) and file_info.get("path") == file_path:
                            files.pop(i)
                            changed = True
                            logger.info(f"[FILE] Dosya referansı silindi: {file_path}")
                            break
        
        # Değişiklik olduysa dosyayı güncelle
        if changed:
            with open(project_file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            return True
        else:
            logger.warning(f"[FILE] Silinecek dosya referansı bulunamadı: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"[FILE] Dosya referansı silinirken hata: {str(e)}", exc_info=True)
        return False

@app.post("/project/{project_name}/remove-file", response_model=dict)
async def remove_file(
 project_name: str,
 component: str = Form(...),
 question_id: str = Form(...),
 filename: str = Form(...),
 file_path: str = Form(...)
):
    """Remove a file object from project JSON array."""
    component_name = component          # keep backward compatibility
    path = file_path                   # alias for helper

    success = remove_file_entry_from_array(project_name, component_name, question_id,
                                         {"filename": filename, "path": path})
    
    if not success:
        raise HTTPException(status_code=500, detail="Dosya silinemedi")
        
    # Güncel dosya listesi
    project_path = get_project_path(project_name)
    with open(project_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    files = []
    active_report = data.get("active_report", {})
    if active_report:
        components = active_report.get("components", {})
        component_data = components.get(component, {})
        answers = component_data.get("answers", {})
        files = answers.get(question_id, [])
        
    return {"success": True, "files": files}