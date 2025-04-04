"""
Raporlama Otomasyonu - Rapor Üretim Modülü

Bu modül, toplanan verilere göre rapor oluşturma ve PDF formatına çevirme işlemlerini yönetir.
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# PDF oluşturma için gerekli kütüphaneler
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Loglama ayarları
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Eğer handler eklenmemişse ekleyelim
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Dosyaya da logları kaydedelim
    log_dir = Path(__file__).parent.parent / "logs"
    if not log_dir.exists():
        os.makedirs(log_dir)
    file_handler = logging.FileHandler(log_dir / "report_generator.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Dosya yolları
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

# Rapor dizinini oluştur
if not REPORTS_DIR.exists():
    os.makedirs(REPORTS_DIR)

# Türkçe font desteği için
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', str(BASE_DIR / 'resources' / 'fonts' / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(BASE_DIR / 'resources' / 'fonts' / 'DejaVuSans-Bold.ttf')))
    logger.info("Türkçe fontlar başarıyla yüklendi")
except Exception as e:
    logger.error(f"Türkçe fontlar yüklenirken hata: {e}")
    logger.warning("Standart fontlar kullanılacak")

def generate_report_content(project_name: str, component_data: Dict[str, Dict[str, str]]) -> str:
    """
    Proje ve bileşen verilerine göre rapor içeriği oluşturur.
    
    Args:
        project_name: Proje adı
        component_data: Bileşen adları ve cevaplar
        
    Returns:
        Oluşturulan rapor içeriği (HTML formatında)
        
    Raises:
        ValueError: Geçersiz veri formatı veya eksik veri durumunda
    """
    logger.info(f"'{project_name}' projesi için rapor içeriği oluşturuluyor")
    
    if not component_data:
        logger.warning(f"'{project_name}' projesi için bileşen verisi boş")
        component_data = {}
    
    try:
        # Rapor şablonu
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        
        report_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Proje Raporu - {project_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; }}
                h1 {{ color: #2c3e50; text-align: center; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }}
                .date {{ color: #7f8c8d; font-style: italic; text-align: right; }}
            </style>
        </head>
        <body>
            <h1>{project_name} Projesi Raporu</h1>
            <p class="date">Oluşturulma Tarihi: {current_date}</p>
        """
        
        # Her bileşen için ayrı bölüm ekle
        for component_name, answers in component_data.items():
            logger.debug(f"'{project_name}' - '{component_name}' bileşeni ekleniyor")
            
            report_content += f"""
            <div class="section">
                <h2>{component_name}</h2>
            """
            
            # Cevapları ekle
            if isinstance(answers, dict) and answers:
                for question_id, answer in answers.items():
                    report_content += f"""
                    <p><strong>Soru {question_id}:</strong> {answer}</p>
                    """
            else:
                report_content += "<p>Bu bileşen için veri bulunmamaktadır.</p>"
            
            report_content += "</div>"
        
        # Raporu sonlandır
        report_content += """
        </body>
        </html>
        """
        
        logger.info(f"'{project_name}' projesi için rapor içeriği oluşturuldu")
        return report_content
    
    except Exception as e:
        logger.error(f"Rapor oluşturulurken hata: {e}")
        raise ValueError(f"Rapor içeriği oluşturulurken bir hata oluştu: {str(e)}")

def generate_pdf(project_name: str, report_content: str) -> str:
    """
    Oluşturulan rapor içeriğinden PDF dosyası oluşturur.
    
    Args:
        project_name: Proje adı
        report_content: Rapor içeriği (HTML formatında)
        
    Returns:
        Oluşturulan PDF dosyasının yolu
        
    Raises:
        ValueError: PDF oluşturulurken hata oluşması durumunda
    """
    logger.info(f"'{project_name}' projesi için PDF oluşturuluyor")
    
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"{project_name}_rapor_{current_date}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename
    
    try:
        # PDF dokümanı oluştur
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Stil ve içerik hazırlığı
        styles = getSampleStyleSheet()
        
        # Türkçe karakter desteği için özel stil
        try:
            styles.add(ParagraphStyle(
                name='TurkishNormal',
                fontName='DejaVuSans',
                fontSize=10,
                leading=12
            ))
            styles.add(ParagraphStyle(
                name='TurkishHeading1',
                fontName='DejaVuSans-Bold',
                fontSize=18,
                leading=22,
                alignment=1  # Ortalanmış
            ))
            styles.add(ParagraphStyle(
                name='TurkishHeading2',
                fontName='DejaVuSans-Bold',
                fontSize=14,
                leading=18
            ))
            
            heading1_style = styles['TurkishHeading1']
            heading2_style = styles['TurkishHeading2']
            normal_style = styles['TurkishNormal']
            
            logger.info("Türkçe stillerle PDF oluşturuluyor")
        except Exception as e:
            # Türkçe fontlar yüklenemediyse standart stilleri kullan
            logger.warning(f"Türkçe stiller oluşturulurken hata: {e}")
            heading1_style = styles['Heading1']
            heading2_style = styles['Heading2']
            normal_style = styles['Normal']
            
            logger.warning("Standart stillerle PDF oluşturuluyor")
        
        # PDF içeriği
        elements = []
        
        # Başlık
        title = f"{project_name} Projesi Raporu"
        elements.append(Paragraph(title, heading1_style))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Tarih
        date_text = f"Oluşturulma Tarihi: {datetime.datetime.now().strftime('%d.%m.%Y')}"
        elements.append(Paragraph(date_text, normal_style))
        elements.append(Spacer(1, 0.5 * inch))
        
        # HTML içeriğinden veri çıkart (basit bir parser)
        # Bu örnekte sadece bileşen başlıkları ve içeriklerini alıyoruz
        try:
            # HTML içeriğini parçala
            parts = report_content.split('<div class="section">')
            
            for i, part in enumerate(parts):
                if i == 0:  # İlk kısım başlık ve tarih bilgilerini içerir, bunu atla
                    continue
                
                # Bölüm başlığını bul
                title_start = part.find('<h2>') + 4
                title_end = part.find('</h2>')
                if title_start > 4 and title_end > 0:
                    component_title = part[title_start:title_end].strip()
                    elements.append(Paragraph(component_title, heading2_style))
                    elements.append(Spacer(1, 0.25 * inch))
                
                # Soru cevaplarını bul ve ekle
                if '<p><strong>' in part:
                    answers = part.split('<p><strong>')
                    for answer in answers:
                        if '</strong>' in answer:
                            qa_pair = answer.split('</strong>')[0] + ': ' + answer.split('</strong>')[1].split('</p>')[0]
                            elements.append(Paragraph(qa_pair, normal_style))
                            elements.append(Spacer(1, 0.1 * inch))
                
                # Bileşenler arasına boşluk ekle
                elements.append(Spacer(1, 0.3 * inch))
        
        except Exception as e:
            logger.error(f"HTML parsing hatası: {e}")
            # Hata durumunda tüm içeriği düz metin olarak ekle
            elements.append(Paragraph("Rapor içeriği işlenirken bir hata oluştu. Ham içerik:", normal_style))
            elements.append(Spacer(1, 0.2 * inch))
            
            # HTML etiketlerini temizle
            clean_content = report_content.replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(clean_content, normal_style))
        
        # PDF'i oluştur
        doc.build(elements)
        
        logger.info(f"PDF başarıyla oluşturuldu: {pdf_path}")
        return str(pdf_path)
    
    except Exception as e:
        logger.error(f"PDF oluşturulurken hata: {e}")
        raise ValueError(f"PDF oluşturulurken bir hata oluştu: {str(e)}") 