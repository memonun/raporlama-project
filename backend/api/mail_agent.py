import smtplib
from email.message import EmailMessage
import os
from config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, DEPARTMENT_EMAILS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from .template_helper import render_template, get_current_year

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
        logo_path = os.path.join(base_dir, "static", "assets", "placeholder_logo.png")
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