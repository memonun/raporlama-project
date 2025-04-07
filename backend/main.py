from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import jinja2
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
import os
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
from api.gpt_handler import generate_report, process_report_request, extract_pdf_content, get_project_reports
from api.mail_agent import send_missing_info_request, get_department_email
from api.questions_handler import get_questions_for_component
from api.data_storage import (
    save_component_data, get_project_data, get_all_projects, 
    save_generated_report, delete_project_data, archive_project, 
    get_active_report, create_new_report, delete_report as delete_report_from_storage, get_report_id,
    finalize_report, get_project_path
)
from models.report_schema import ReportData, ComponentStatus
from fastapi.staticfiles import StaticFiles
import json
import datetime
import shutil
import tempfile
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from config import PROJECT_PALETTES, CORPORATE_COLORS
import base64
import logging

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

# Modeller
class ProjectRequest(BaseModel):
    project_name: str

class ReportRequest(BaseModel):
    project_name: str

class ComponentDataRequest(BaseModel):
    project_name: str
    component_name: str
    answers: Dict[str, str]

class GenerateReportRequest(BaseModel):
    project_name: str
    components_data: Dict[str, Dict[str, Any]] = {}
    user_input: Optional[str] = None
    pdf_content: Optional[str] = None

class EmailRequest(BaseModel):
    component_name: str
    project_name: str

class MissingInfoRequest(BaseModel):
    project_name: str
    component_name: str
    recipient_name: str

class ProjectActionRequest(BaseModel):
    project_name: str

class ShareReportRequest(BaseModel):
    project_name: str
    email_addresses: List[str]

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
        report_id = get_report_id(request.project_name)
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

@app.post("/project/generate-report", response_model=Dict[str, Any])
async def generate_project_report(request: GenerateReportRequest):
    """
    Proje verilerini, kullanıcı girdilerini ve PDF içeriklerini kullanarak
    GPT ile rapor oluşturur, stilize PDF olarak kaydeder ve sonucu döndürür.
    """
    logger.info(f"[REPORT_GEN] Rapor oluşturma isteği alındı: Proje={request.project_name}")
    try:
        # Bileşen verilerini kontrol et
        logger.info(f"[REPORT_GEN] Bileşen verileri kontrol ediliyor...")
        if not request.components_data:
            logger.error(f"[REPORT_GEN] Hata: Bileşen verileri boş. Proje={request.project_name}")
            raise HTTPException(
                status_code=400, 
                detail="Bileşen verileri bulunamadı. Lütfen en az bir bileşen için veri sağlayın."
            )
        logger.info(f"[REPORT_GEN] Bileşen verileri geçerli.")

        # 1. Metin içeriğini oluştur (GPT çağrısı)
        logger.info(f"[REPORT_GEN] GPT ile rapor içeriği oluşturuluyor... Proje={request.project_name}")
        try:
            report_content_text = generate_report(
                request.project_name,
                request.components_data,
                request.user_input
            )
            logger.info(f"[REPORT_GEN] GPT rapor içeriği başarıyla oluşturuldu.")
        except Exception as gpt_error:
            logger.error(f"[REPORT_GEN] GPT çağrısı sırasında hata: {gpt_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Yapay zeka ile rapor oluşturulurken hata: {gpt_error}")

        # Rapor ID'si oluştur
        logger.info(f"[REPORT_GEN] Rapor ID alınıyor...")
        report_id = get_report_id(request.project_name)
        logger.info(f"[REPORT_GEN] Rapor ID alındı: {report_id}")

        # 2. Rapora görsel/stil özellikleri ekleyerek PDF oluştur
        logger.info(f"[REPORT_GEN] PDF oluşturma süreci başlıyor...")
        # 2.1 Projeye özel renkleri ve görsel bilgilerini al
        logger.info(f"[REPORT_GEN] Proje renkleri alınıyor...")
        project_colors = get_project_colors(request.project_name)
        logger.info(f"[REPORT_GEN] Proje renkleri alındı.")
        
        # 2.2 Görseli belirle
        logger.info(f"[REPORT_GEN] Proje görseli belirleniyor...")
        report_image_filename = f"{request.project_name.lower()}-inşaat-1.jpg"
        image_data_uri = get_image_path_or_data(request.project_name, report_image_filename)
        logger.info(f"[REPORT_GEN] Proje görseli belirlendi: {report_image_filename if image_data_uri else 'Görsel Yok'}")
        
        # 2.3 Jinja2 şablonunu yükle ve render et
        logger.info(f"[REPORT_GEN] Jinja2 şablonu yükleniyor ve render ediliyor...")
        try:
            template = env.get_template('report_template.html')
            html_content = template.render(
                project_name=request.project_name,
                report_data=report_content_text,  # AI'dan gelen metin içeriği
                project_colors=project_colors,
                corporate_colors=CORPORATE_COLORS,
                project_image=image_data_uri
            )
            logger.info(f"[REPORT_GEN] Jinja2 şablonu başarıyla render edildi.")
        except jinja2.exceptions.TemplateNotFound:
            logger.warning(f"[REPORT_GEN] Uyarı: Rapor şablonu 'report_template.html' bulunamadı, basit HTML oluşturuluyor.")
            # Fallback HTML creation
            html_content = f"<html><body><h1>{request.project_name} Raporu</h1>{report_content_text}</body></html>"
        except Exception as render_error:
             logger.error(f"[REPORT_GEN] Jinja2 render sırasında hata: {render_error}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Rapor şablonu işlenirken hata: {render_error}")

        # 2.4 WeasyPrint ile HTML'den PDF oluştur
        logger.info(f"[REPORT_GEN] WeasyPrint ile PDF oluşturuluyor...")
        font_config = FontConfiguration()
        css = CSS(string='@page { size: A4; margin: 1.5cm; @bottom-left { content: "İsra Holding"; font-size: 9pt; color: #666; } @bottom-right { content: "Sayfa " counter(page) " / " counter(pages); font-size: 9pt; color: #666; } }', font_config=font_config)
        css_file_path = template_dir / 'style.css'
        
        try:
            html = HTML(string=html_content, base_url=str(template_dir))
            stylesheets = [css]
            if css_file_path.is_file():
                logger.info(f"[REPORT_GEN] Stil dosyası kullanılıyor: {css_file_path}")
                stylesheets.append(CSS(filename=str(css_file_path)))
            else:
                logger.warning(f"[REPORT_GEN] Stil dosyası bulunamadı: {css_file_path}, sadece temel CSS kullanılıyor.")
                
            pdf_bytes = html.write_pdf(stylesheets=stylesheets, font_config=font_config)
            logger.info(f"[REPORT_GEN] WeasyPrint PDF başarıyla oluşturuldu (bytes: {len(pdf_bytes)})." )
            
            # 2.5 PDF'i dosyaya kaydet
            logger.info(f"[REPORT_GEN] PDF dosyası kaydediliyor...")
            reports_dir = Path("data") / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            pdf_filename = f"{request.project_name}_{report_id}.pdf"
            pdf_path = reports_dir / pdf_filename
            
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"[REPORT_GEN] PDF dosyası başarıyla kaydedildi: {pdf_path}")
            
            # Rapor meta verilerini kaydet
            logger.info(f"[REPORT_GEN] Rapor meta verileri kaydediliyor...")
            result = save_generated_report(
                request.project_name,
                report_id,
                report_content_text,
                str(pdf_path)
            )
            logger.info(f"[REPORT_GEN] Rapor meta verileri başarıyla kaydedildi.")
            
            logger.info(f"[REPORT_GEN] Rapor oluşturma başarıyla tamamlandı. Proje={request.project_name}, ID={report_id}, Path={pdf_path}")
            return result
            
        except Exception as pdf_error:
            logger.error(f"[REPORT_GEN] WeasyPrint PDF oluşturma/kaydetme sırasında hata: {pdf_error}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"PDF oluşturulurken veya kaydedilirken bir hata oluştu: {str(pdf_error)}"
            )
            
    except HTTPException as http_exc: # Re-raise HTTP exceptions directly
        # Logging for HTTP exceptions is already done where they are raised
        raise http_exc
    except Exception as e:
        logger.error(f"[REPORT_GEN] Genel rapor oluşturma hatası: Proje={request.project_name}, Hata: {e}", exc_info=True)
        error_message = str(e)
        # ... (rest of the general error handling)
        raise HTTPException(
            status_code=500,
            detail=f"Rapor oluşturulurken beklenmedik bir hata oluştu: {error_message}"
        )

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
            
        pdf_path = active_report.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise FileNotFoundError("PDF dosyası bulunamadı")
            
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

class DeleteReportRequest(BaseModel):
    project_name: str

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

class DeleteProjectRequest(BaseModel):
    project_name: str

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

class ArchiveProjectRequest(BaseModel):
    project_name: str

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

@app.post("/process-report")
async def process_report(
    user_input: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None)
):
    """
    Kullanıcının metin ve/veya PDF dosyasını işler ve sonuçlarını döndürür.
    Dosya işleme, OpenAI API kullanılarak gerçekleştirilir.
    """
    if not user_input and not pdf_file:
        raise HTTPException(status_code=400, detail="Metin veya PDF dosyası gereklidir")
    
    try:
        # PDF dosyasını geçici olarak kaydet
        temp_file_path = None
        if pdf_file:
            try:
                # PDF dosyasını oku
                content = await pdf_file.read()
                if not content:
                    raise HTTPException(status_code=400, detail="Yüklenen PDF dosyası boş")
                
                # Dosya boyutunu kontrol et
                file_size = len(content)
                if file_size == 0:
                    raise HTTPException(status_code=400, detail="PDF dosyası boş")
                print(f"PDF dosyası boyutu: {file_size} byte")
                
                # Geçici dosya oluştur
                import tempfile
                import os
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file_path = temp_file.name
                temp_file.write(content)
                temp_file.close()
                
                # Dosya kontrolü
                if not os.path.exists(temp_file_path):
                    raise HTTPException(status_code=400, detail="PDF dosyası geçici olarak kaydedilemedi")
                
                file_saved_size = os.path.getsize(temp_file_path)
                if file_saved_size == 0:
                    os.unlink(temp_file_path)
                    raise HTTPException(status_code=400, detail="Kaydedilen PDF dosyası boş")
                    
                print(f"PDF dosyası geçici olarak kaydedildi: {temp_file_path} ({file_saved_size} byte)")
            except HTTPException as e:
                # HTTP hataları yukarıya ilet
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise e
            except Exception as e:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                print(f"PDF dosyası işlenirken hata: {str(e)}")
                raise HTTPException(status_code=400, detail=f"PDF dosyası işlenirken hata: {str(e)}")
        
        # İşlem parametrelerini hazırla
        process_params = {}
        if user_input:
            process_params['user_input'] = user_input
            print(f"Kullanıcı metni: {user_input[:50]}...")
        
        if temp_file_path:
            try:
                # PDF içeriğini çıkar
                pdf_content = extract_pdf_content(temp_file_path)
                if not pdf_content or pdf_content.strip() == "":
                    raise HTTPException(status_code=400, detail="PDF içeriği çıkarılamadı veya PDF boş")
                
                process_params['pdf_content'] = pdf_content
                print(f"PDF içeriği çıkarıldı: {len(pdf_content)} karakter")
            except Exception as e:
                print(f"PDF içeriği çıkarılırken hata: {str(e)}")
                raise HTTPException(status_code=400, detail=f"PDF içeriği çıkarılırken hata: {str(e)}")
            finally:
                # Geçici dosyayı temizle
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    print(f"Geçici dosya silindi: {temp_file_path}")
        
        # Rapor işleme
        try:
            result = await process_report_request(**process_params)
            
            # Sonuç kontrolü
            if not result:
                raise HTTPException(status_code=500, detail="İşlem sonucu boş")
                
            if "error" in result and result["error"]:
                raise HTTPException(status_code=500, detail=result["error"])
                
            # PDF yolunu daha erişilebilir yap
            if result.get('pdf_path'):
                result['download_url'] = f"/download/{result['pdf_path']}"
            
            return result
        except HTTPException as e:
            # HTTP hataları yukarıya ilet
            raise e
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Rapor işlenirken beklenmeyen hata: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Rapor işlenirken hata oluştu: {str(e)}")
    except HTTPException as e:
        # Önceden oluşturulan HTTP hataları
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Rapor işlenirken beklenmeyen hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rapor işlenirken hata oluştu: {str(e)}")

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
        return {"success": True, "message": "Rapor başarıyla sonlandırıldı", "report_data": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {request.project_name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor sonlandırılırken hata oluştu: {str(e)}")

@app.get("/project/{project_name}/unfinalized-reports")
def get_unfinalized_reports(project_name: str):
    """Bir projeye ait tamamlanmamış raporları getirir."""
    try:
        # Projeye ait raporları al
        reports = get_project_reports(project_name)
        
        # Tamamlanmamış raporları filtrele
        unfinalized_reports = [report for report in reports if report.get("is_finalized") == False]
        
        return {"reports": unfinalized_reports}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Tamamlanmamış raporlar getirilirken bir hata oluştu: {str(e)}")

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
            
        # PDF yolu var mı ve dosya mevcut mu kontrol et
        pdf_path = target_report.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"HATA: PDF dosyası bulunamadı. Beklenen yol: {pdf_path}") # Loglama için
            raise HTTPException(status_code=404, detail="Raporun PDF dosyası sunucuda bulunamadı")
            
        # Dosyayı döndür
        filename = f"{project_name}_{report_id}_report.pdf"
        return FileResponse(
            path=pdf_path,
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

class DeleteFinalizedReportRequest(BaseModel):
    project_name: str
    file_name: str

@app.post("/project/delete-finalized-report", response_model=Dict[str, Any])
def delete_finalized_report(request: DeleteFinalizedReportRequest):
    """Bir projenin sonlandırılmış raporlarından birini siler."""
    try:
        project_name = request.project_name
        file_name = request.file_name
        
        # Proje kontrolü
        project_data = get_project_data(project_name)
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_name}")
        
        # Finalized rapor listesini kontrol et
        finalized_reports = project_data.get("reports", [])
        
        # Verilen dosya adıyla eşleşen finalized raporu bul
        found_report = None
        for report in finalized_reports:
            if report.get("is_finalized") and (report.get("name") == file_name or report.get("report_id") == file_name):
                found_report = report
                break
        
        if not found_report:
            raise HTTPException(status_code=404, detail=f"Belirtilen finalized rapor bulunamadı: {file_name}")
        
        # PDF dosyasının yolunu al
        pdf_path = found_report.get("pdf_path")
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"Rapor için PDF dosyası bulunamadı")
        
        # PDF dosyasını ve finalized raporu sil
        try:
            # PDF dosyasını sil
            full_path = Path(pdf_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"PDF dosyası silindi: {full_path}")
            
            # Finalized raporu proje verilerinden kaldır
            finalized_reports.remove(found_report)
            project_data["reports"] = finalized_reports
            project_data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Güncellenmiş proje verilerini kaydet
            with open(get_project_path(project_name), 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            return {
                "message": "Finalized rapor başarıyla silindi", 
                "project_name": project_name,
                "file_name": file_name
            }
        except Exception as e:
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
    
    Args:
        file: Yüklenecek PDF dosyası
        
    Returns:
        Çıkarılan metin içeriği
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
            extracted_content = extract_pdf_content(temp_file.name)
            
            # İçeriği JSON olarak döndür
            return {"content": extracted_content}
        finally:
            # Geçici dosyayı temizle
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Geçici dosya silinirken hata: {e}")
    except Exception as e:
        # Orijinal hatayı koru - eğer HTTP hatası ise
        if isinstance(e, HTTPException):
            raise e
        
        # Diğer hataları logla ve genel bir hata mesajı döndür
        print(f"PDF içeriği çıkarılırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF içeriği çıkarılamadı: {str(e)}")

@app.post("/api/extract-pdf")
async def extract_pdf_api_endpoint(file: UploadFile = File(...)):
    """
    PDF dosyasından içerik çıkarır ve metin olarak döndürür.
    /api/ prefix'i ile aynı işlevselliği sunar.
    
    Args:
        file: Yüklenecek PDF dosyası
        
    Returns:
        Çıkarılan metin içeriği
    """
    return await extract_pdf_endpoint(file)

# Jinja2 ortamını ayarla
template_dir = Path(__file__).parent / 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

# Statik dosya yolu (görseller için)
STATIC_DIR = Path(__file__).parent / 'static'
IMAGES_DIR = STATIC_DIR / 'images'

# Renk paletini getir
def get_project_colors(project_name):
    return PROJECT_PALETTES.get(project_name.lower(), {})

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 