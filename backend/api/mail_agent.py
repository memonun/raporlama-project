import smtplib
from email.message import EmailMessage
import os
from config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, DEPARTMENT_EMAILS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from .template_helper import render_template, get_current_year
from typing import List
from fastapi import HTTPException
import logging
from utils.pdf_utils import get_report_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_missing_info_request(to_email: str, project_name: str = None, component_name: str = None) -> str:
    """
    Belirtilen departman e-posta adresine yatırımcı raporu bilgi talebi gönderir.
    
    Args:
        to_email: Alıcı departman e-posta adresi
        project_name: (Opsiyonel) Proje adı
        component_name: (Opsiyonel) Bileşen adı
        
    Returns:
        Gönderim durumu bilgisi
    """
    msg = EmailMessage()
    subject = "Yatırımcı Raporu: Bilgi Talebi"
    
    if project_name:
        subject += f" - {project_name}"
    
    if component_name:
        subject += f" ({component_name} Bileşeni)"
    
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    
    # Proje bilgisi
    project_display = project_name if project_name else "ilgili proje"
    component_display = component_name if component_name else "ilgili bileşen"
    
    # CID referansları oluştur
    from email.utils import make_msgid
    logo_cid = make_msgid(domain='israholding.com.tr')
    cover_cid = make_msgid(domain='israholding.com.tr')
    
    # Template'i işle ve e-posta içeriğini oluştur
    template_variables = {
        'project_display': project_display,
        'component_display': component_display,
        'logo_cid': logo_cid,
        'cover_cid': cover_cid
    }
    
    # HTML ve düz metin içeriklerini oluştur
    html_content = render_template('info_request', 'html', **template_variables)
    plain_text = render_template('info_request', 'txt', **template_variables)
    
    # Temel içerik olarak plain text ekle
    msg.set_content(plain_text)
    
    # HTML alternatifi ekle
    msg.add_alternative(html_content, subtype='html')
    
    # Logo ve kapak resimlerini ekle
    add_images_to_email(msg, logo_cid, cover_cid)
    
    try:
        # SMTP bağlantısı kur ve mail gönder
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return f"E-posta başarıyla gönderildi: {to_email}"
    
    except smtplib.SMTPAuthenticationError:
        raise Exception("E-posta kimlik doğrulama hatası. Kullanıcı adı ve şifrenizi kontrol edin. Gmail kullanıyorsanız, uygulama şifresi kullanmanız gerekebilir.")
    except smtplib.SMTPServerDisconnected:
        raise Exception("SMTP sunucusu bağlantısı kesildi. Sunucu ayarlarınızı kontrol edin.")
    except smtplib.SMTPException as e:
        raise Exception(f"SMTP hatası: {str(e)}")
    except Exception as e:
        raise Exception(f"E-posta gönderilirken hata oluştu: {str(e)}")

def add_images_to_email(msg, logo_cid, cover_cid):
    """
    E-postaya resim ekler
    
    Args:
        msg: EmailMessage nesnesi
        logo_cid: Logo için content ID
        cover_cid: Kapak resmi için content ID
    """
    import os
    from pathlib import Path
    
    # Proje kök dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = Path(current_dir).parent
    
    # Logo ve kapak resim dosyaları için yollar
    logo_path = os.path.join(base_dir, "static", "assets", "logo.png")
    cover_path = os.path.join(base_dir, "static", "assets", "cover.png")
    
    # Logo dosyası yoksa placeholder kullan
    if not os.path.exists(logo_path):
        logo_path = os.path.join(base_dir, "data", "project_assets", "isra_logo.png")
        # Placeholder da yoksa ekleme
        if not os.path.exists(logo_path):
            print(f"Uyarı: Logo dosyası bulunamadı: {logo_path}")
            return
    
    # Kapak dosyası yoksa placeholder kullan
    if not os.path.exists(cover_path):
        cover_path = os.path.join(base_dir, "static", "assets", "placeholder_cover.png")
        # Placeholder da yoksa ekleme
        if not os.path.exists(cover_path):
            print(f"Uyarı: Kapak görseli bulunamadı: {cover_path}")
            return
    
    # Logo ekle
    with open(logo_path, 'rb') as img:
        logo_data = img.read()
        img_subtype = 'png' if logo_path.endswith('.png') else 'jpeg'
        msg.add_related(logo_data, 
                       maintype='image',
                       subtype=img_subtype,
                       cid=logo_cid[1:-1])  # CID'den < ve > karakterlerini kaldır
    
    # Kapak ekle
    with open(cover_path, 'rb') as img:
        cover_data = img.read()
        img_subtype = 'png' if cover_path.endswith('.png') else 'jpeg'
        msg.add_related(cover_data, 
                       maintype='image',
                       subtype=img_subtype,
                       cid=cover_cid[1:-1])  # CID'den < ve > karakterlerini kaldır

def get_department_email(component_name: str) -> str:
    """
    Bileşen adına göre ilgili departmanın e-posta adresini döndürür.
    
    Args:
        component_name: Bileşen adı
        
    Returns:
        Departman e-posta adresi
    """
    return DEPARTMENT_EMAILS.get(component_name, EMAIL_SENDER)

def send_report_email(project_name: str, report_id: str, email_addresses: List[str]) -> dict:
    """Send a report to specified email addresses."""
    logger.info(f"[MAIL_AGENT] Starting send_report_email for project: {project_name}, report_id: {report_id}")
    logger.info(f"[MAIL_AGENT] Target email addresses: {email_addresses}")

    try:
        # Get the report file path using the centralized utility
        logger.info(f"[MAIL_AGENT] Getting report path for project: {project_name}, report_id: {report_id} using pdf_utils")
        report_path_obj = get_report_path(project_name, report_id) # Returns a Path object
        report_path = str(report_path_obj) # Convert to string if needed by os.path.exists or open
        logger.info(f"[MAIL_AGENT] Report path resolved to: {report_path}")

        # Use the string path for os.path.exists
        if not os.path.exists(report_path):
            logger.error(f"[MAIL_AGENT] Report file not found at path: {report_path}")
            # Raise FileNotFoundError instead of generic Exception
            raise FileNotFoundError(f"Report PDF file not found at path: {report_path}")

        logger.info(f"[MAIL_AGENT] Report file exists and is accessible")

        # Create email message
        logger.info("[MAIL_AGENT] Creating email message")
        msg = MIMEMultipart()
        msg["Subject"] = f"İsra Holding - {project_name} Projesi Raporu"
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(email_addresses)
        logger.info(f"[MAIL_AGENT] Email headers set - Subject: {msg['Subject']}, From: {msg['From']}, To: {msg['To']}")

        # Add email body
        logger.info("[MAIL_AGENT] Adding email body")
        body = f"""
        Sayın İlgili,

        {project_name} projesi için oluşturulan raporu ekte bulabilirsiniz.

        Saygılarımızla,
        İSRA HOLDİNG
        """
        msg.attach(MIMEText(body, "plain"))
        logger.info("[MAIL_AGENT] Email body attached successfully")

        # Attach the PDF - open can handle Path objects or strings
        logger.info(f"[MAIL_AGENT] Attempting to attach PDF file: {report_path}")
        try:
            # Using report_path_obj (Path object) directly with open
            with open(report_path_obj, "rb") as f:
                pdf_content = f.read()
                pdf_size = len(pdf_content)
                logger.info(f"[MAIL_AGENT] PDF file read successfully. Size: {pdf_size} bytes")
                
                pdf = MIMEApplication(pdf_content, _subtype="pdf")
                pdf.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=f"{project_name}_rapor.pdf"
                )
                msg.attach(pdf)
                logger.info("[MAIL_AGENT] PDF attached to email successfully")
        except Exception as pdf_error:
            logger.error(f"[MAIL_AGENT] Error attaching PDF: {str(pdf_error)}")
            raise Exception(f"Failed to attach PDF: {str(pdf_error)}")

        # Send email
        logger.info(f"[MAIL_AGENT] Attempting to connect to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                logger.info("[MAIL_AGENT] SMTP connection established")
                
                logger.info("[MAIL_AGENT] Starting TLS")
                server.starttls()
                logger.info("[MAIL_AGENT] TLS started successfully")
                
                logger.info("[MAIL_AGENT] Attempting SMTP login")
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                logger.info("[MAIL_AGENT] SMTP login successful")
                
                logger.info("[MAIL_AGENT] Sending email")
                server.send_message(msg)
                logger.info("[MAIL_AGENT] Email sent successfully")
        except smtplib.SMTPAuthenticationError as auth_error:
            logger.error(f"[MAIL_AGENT] SMTP Authentication failed: {str(auth_error)}")
            raise Exception("Email authentication failed")
        except smtplib.SMTPException as smtp_error:
            logger.error(f"[MAIL_AGENT] SMTP error occurred: {str(smtp_error)}")
            raise Exception(f"SMTP error: {str(smtp_error)}")
        except Exception as send_error:
            logger.error(f"[MAIL_AGENT] Unexpected error during email sending: {str(send_error)}")
            raise Exception(f"Failed to send email: {str(send_error)}")

        logger.info("[MAIL_AGENT] Email process completed successfully")
        return {"message": "Report sent successfully"}

    except FileNotFoundError as e:
        logger.error(f"[MAIL_AGENT] File not found error during email process: {str(e)}")
        # Re-raise FileNotFoundError so the endpoint can catch it specifically
        raise e
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[MAIL_AGENT] SMTP Authentication error: {str(e)}")
        # Wrap SMTP auth errors in a specific exception if needed, or re-raise/raise generic
        raise Exception("Email authentication failed") # Or raise a custom exception
    except Exception as e:
        logger.error(f"[MAIL_AGENT] Unexpected error during email send: {str(e)}")
        # Re-raise other exceptions or wrap them
        raise Exception(f"An unexpected error occurred while sending the report email: {str(e)}") 