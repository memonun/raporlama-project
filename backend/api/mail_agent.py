import smtplib, ssl
from email.message import EmailMessage
import os
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List
from fastapi import HTTPException
import logging

# Email configuration - matching your test script exactly
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_SENDER = "report@israholding.com.tr"
EMAIL_PASSWORD = "Isra020150!"

# Department email mappings
DEPARTMENT_EMAILS = {
    'İşletme': 'ozdassuleyman123@gmail.com',  # For testing
    'Finans': 'ozdassuleyman123@gmail.com',
    'İnşaat': 'ozdassuleyman123@gmail.com',
    'Kurumsal İletişim': 'ozdassuleyman123@gmail.com',
    'default': 'ozdassuleyman123@gmail.com'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_missing_info_request(to_email: str, project_name: str = None, component_name: str = None) -> str:
    """
    Send information request email - simplified version matching the working test script
    """
    logger.info(f"[MAIL] Starting send_missing_info_request to: {to_email}")
    
    try:
        # Create EmailMessage exactly like the test script
        msg = EmailMessage()
        
        # Build subject
        subject = "Yatırımcı Raporu: Bilgi Talebi"
        if project_name:
            subject += f" - {project_name}"
        if component_name:
            subject += f" ({component_name} Bileşeni)"
        
        # Set headers exactly like test script
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        
        # Simple content
        project_display = project_name if project_name else "ilgili proje"
        component_display = component_name if component_name else "ilgili bileşen"
        
        content = f"""Sayın İlgili,

{project_display} için yatırımcı raporundaki {component_display} bileşenine ait eksik bilgilerin tamamlanması rica olunur, iyi çalışmalar.

Saygılarımızla,
İSRA HOLDİNG

Yardım talepleriniz için: israreport@israholding.com.tr"""
        
        # Set content exactly like test script
        msg.set_content(content)
        
        # Create SSL context exactly like test script
        context = ssl.create_default_context()
        
        # Send email exactly like test script
        logger.info(f"[MAIL] Connecting to {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            logger.info("[MAIL] Logging in...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            logger.info("[MAIL] Sending message...")
            server.send_message(msg)
            logger.info("[MAIL] ✉️ E-posta gönderildi!")
        
        return f"E-posta başarıyla gönderildi: {to_email}"
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[MAIL] ❌ Auth hatası: {e}")
        raise Exception(f"E-posta kimlik doğrulama hatası: {str(e)}")
    except Exception as e:
        logger.error(f"[MAIL] ⚠️ Başka bir hata: {type(e).__name__}: {e}")
        raise Exception(f"E-posta gönderilirken hata oluştu: {str(e)}")

def get_department_email(component_name: str) -> str:
    """
    Get department email based on component name
    """
    email = DEPARTMENT_EMAILS.get(component_name, DEPARTMENT_EMAILS.get('default', EMAIL_SENDER))
    logger.info(f"[MAIL] Department email for '{component_name}': {email}")
    return email

def send_report_email(project_name: str, report_id: str, email_addresses: List[str]) -> dict:
    """Send a report to specified email addresses - using simple EmailMessage"""
    logger.info(f"[MAIL_AGENT] Starting send_report_email for project: {project_name}, report_id: {report_id}")
    logger.info(f"[MAIL_AGENT] Target email addresses: {email_addresses}")

    try:
        # Import here to avoid circular import
        from utils.pdf_utils import get_report_path
        
        # Get the report file path
        logger.info(f"[MAIL_AGENT] Getting report path for project: {project_name}, report_id: {report_id}")
        report_path_obj = get_report_path(project_name, report_id)
        report_path = str(report_path_obj)
        logger.info(f"[MAIL_AGENT] Report path resolved to: {report_path}")

        if not os.path.exists(report_path):
            logger.error(f"[MAIL_AGENT] Report file not found at path: {report_path}")
            raise FileNotFoundError(f"Report PDF file not found at path: {report_path}")

        logger.info(f"[MAIL_AGENT] Report file exists and is accessible")

        # Read PDF content
        with open(report_path, "rb") as f:
            pdf_content = f.read()
            pdf_size = len(pdf_content)
            logger.info(f"[MAIL_AGENT] PDF file read successfully. Size: {pdf_size} bytes")

        # Create EmailMessage (simpler than MIMEMultipart)
        msg = EmailMessage()
        msg["Subject"] = f"İsra Holding - {project_name} Projesi Raporu"
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(email_addresses)
        
        # Set main content
        body = f"""Sayın İlgili,

{project_name} projesi için oluşturulan raporu ekte bulabilirsiniz.

Saygılarımızla,
İSRA HOLDİNG"""
        msg.set_content(body)
        
        # Add PDF attachment
        msg.add_attachment(
            pdf_content,
            maintype='application',
            subtype='pdf',
            filename=f"{project_name}_rapor.pdf"
        )
        
        # Send email
        context = ssl.create_default_context()
        
        logger.info(f"[MAIL_AGENT] Connecting to {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            logger.info("[MAIL_AGENT] Logging in...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            logger.info("[MAIL_AGENT] Sending message...")
            server.send_message(msg)
            logger.info("[MAIL_AGENT] ✉️ E-posta gönderildi!")

        logger.info("[MAIL_AGENT] Email process completed successfully")
        return {"message": "Report sent successfully"}

    except FileNotFoundError as e:
        logger.error(f"[MAIL_AGENT] File not found error: {str(e)}")
        raise e
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[MAIL_AGENT] ❌ SMTP Authentication error: {str(e)}")
        raise Exception(f"Email authentication failed: {str(e)}")
    except Exception as e:
        logger.error(f"[MAIL_AGENT] ⚠️ Unexpected error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")