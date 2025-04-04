from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os
import datetime
from pathlib import Path
from config import REPORTS_DIR
import uuid

def save_report_as_pdf(report_text: str, project_name: str) -> str:
    """
    Rapor metnini PDF olarak kaydeder ve dosya yolunu döndürür.
    
    Args:
        report_text: Rapor metni
        project_name: Proje adı
        
    Returns:
        Oluşturulan PDF dosyasının yolu
    """
    try:
        # Proje dizinini oluştur (raporları proje bazlı saklama için)
        safe_project_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name)
        project_dir = REPORTS_DIR / safe_project_name
        os.makedirs(project_dir, exist_ok=True)
        
        # Benzersiz dosya adı oluştur
        #unique_id = uuid.uuid4().hex[:8]  # 8 karakter yeterli
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        file_name = f"{safe_project_name}__{current_date}.pdf"
        file_path = project_dir / file_name
        
        # PDF belgesini oluştur
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # İçerik için stil ve paragrafları oluştur
        styles = getSampleStyleSheet()
        
        # Özel başlık stili
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12
        )
        
        # Özel paragraf stili
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )
        
        # PDF içeriğini oluştur
        content = []
        
        # Başlık ekle
        title = Paragraph(f"{project_name} Yatırımcı Raporu", title_style)
        content.append(title)
        content.append(Spacer(1, 12))
        
        # Tarih ekle
        date_text = f"Oluşturulma Tarihi: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        date = Paragraph(date_text, styles["Normal"])
        content.append(date)
        content.append(Spacer(1, 24))
        
        # Rapor içeriğini paragraf olarak ekle
        lines = report_text.split('\n')
        for line in lines:
            if not line.strip():
                content.append(Spacer(1, 6))
                continue
                
            # Başlıkları belirle ve stil uygula
            if line.strip().startswith('#'):
                p = Paragraph(line.replace('#', '').strip(), title_style)
            else:
                p = Paragraph(line, normal_style)
                
            content.append(p)
        
        # PDF'i oluştur
        doc.build(content)
        
        return str(file_path)
        
    except Exception as e:
        # Hata durumunda yedekleme yöntemi
        try:
            # Yedekleme dizini
            backup_dir = REPORTS_DIR / "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_name = f"{safe_project_name}_{current_date}_backup.pdf"
            backup_path = backup_dir / backup_name
            
            # Basit PDF oluşturma
            c = canvas.Canvas(str(backup_path), pagesize=letter)
            c.drawString(100, 750, f"{project_name} Yatırımcı Raporu")
            
            y_position = 730
            for line in report_text.split('\n'):
                if y_position < 100:  # Sayfa sonu kontrolü
                    c.showPage()
                    y_position = 750
                
                c.drawString(100, y_position, line[:80])  # Satır uzunluğunu sınırla
                y_position -= 12
            
            c.save()
            return str(backup_path)
            
        except Exception as inner_e:
            raise Exception(f"PDF oluşturulurken hata: {str(e)}. Yedekleme de başarısız: {str(inner_e)}") 