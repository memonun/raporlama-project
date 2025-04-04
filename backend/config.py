import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasını yükle
load_dotenv()

# API anahtarları
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

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
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"

# Dizinleri oluştur
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# GPT modeli ayarları
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4-turbo-preview")
GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", "0.7"))
GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", "4096"))

