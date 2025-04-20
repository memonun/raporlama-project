"""
Backend uygulaması için konfigürasyon ayarları
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Temel dizin yolları
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"

# Dizinlerin mevcut olduğundan emin olmak için
os.makedirs(REPORTS_DIR, exist_ok=True)

# Görsel ve şablon dizinleri
ASSETS_DIR = STATIC_DIR / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"
COLORS_DIR = ASSETS_DIR / "colors"

# Kurumsal renkler


# Proje renk paletleri
def load_project_palettes():
    """
    Proje renk paletlerini yükler, dosya yoksa varsayılan değerleri kullanır
    """
    palette_file = COLORS_DIR / "project_palettes.json"
    
    # Varsayılan palet
    default_palettes = {
        "default": {
            "primary": "#1a5276",
            "secondary": "#2980b9", 
            "background": "#ebf5fb",
            "accent": "#154360"
        }
    }
    
    if not palette_file.exists():
        return default_palettes
        
    try:
        with open(palette_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default_palettes

# PDF oluşturma ayarları
PDF_SETTINGS = {
    "page_size": "A4",
    "margin_top": "2cm",
    "margin_right": "2cm",
    "margin_bottom": "2cm",
    "margin_left": "2cm",
    "encoding": "utf-8"
}

# Email gönderme ayarları
EMAIL_SETTINGS = {
    "api_key": os.getenv("SENDGRID_API_KEY", ""),
    "sender_email": "raporlama@israholding.com",
    "sender_name": "İsra Holding Raporlama",
    "template_dir": TEMPLATES_DIR / "email"
}

# OpenAI API anahtarı
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# SendGrid API anahtarı
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# Proje renk paletlerini yükle
PROJECT_PALETTES = load_project_palettes()

# E-posta ayarları
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "seninemail@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Departman e-postaları
DEPARTMENT_EMAILS = {
    "İşletme": os.getenv("BUSINESS_EMAIL", "isletme@sirket.com"),
    "Finans": os.getenv("FINANCE_EMAIL", "finans@sirket.com"),
    "İnşaat": os.getenv("CONSTRUCTION_EMAIL", "insaat@sirket.com"),
    "Kurumsal İletişim": os.getenv("CORPORATE_EMAIL", "iletisim@sirket.com")
}

# Dosya yolları
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"

# Dizinleri oluştur
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)




