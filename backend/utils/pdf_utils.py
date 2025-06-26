import os
import logging
from typing import Optional, Tuple, List , Dict 
import base64
from pathlib import Path
from datetime import datetime
import tempfile
import pdfplumber
import re
import shutil
import json
from uuid import uuid4
logger = logging.getLogger(__name__)

# Constants
BASE_REPORTS_DIR = Path("data/reports")
BASE_ACTIVE_REPORT_DIR = Path("data/uploads/active_report")
def get_active_report_id(project_name: str) -> str:
    """
    Proje adına göre aktif rapor ID'sini döndürür.
    
    Args:
        project_name: Proje adı
    """
    """
    Proje adına göre aktif rapor ID'sini döndürür.
    
    Args:
        project_name: Proje adı
        
    Returns:
        str: Aktif rapor ID'si veya None (aktif rapor yoksa)
    """
    try:
        # Proje dosyasının yolunu oluştur
        project_file = Path(f"data/projects/{project_name}.json")
        
        # Proje dosyasını oku
        if not project_file.exists():
            logger.warning(f"Proje dosyası bulunamadı: {project_file}")
            return None
            
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            
        # Active report kontrolü
        active_report = project_data.get('active_report')
        if not active_report:
            logger.info(f"Aktif rapor bulunamadı: {project_name}")
            return None
            
        report_id = active_report.get('report_id')
        if not report_id:
            logger.warning(f"Aktif raporda report_id bulunamadı: {project_name}")
            return None
            
        logger.info(f"Aktif rapor ID'si bulundu: {report_id}")
        return report_id
        
    except Exception as e:
        logger.error(f"Aktif rapor ID'si alınırken hata: {str(e)}", exc_info=True)
        return None

def create_report_id(project_name: str) -> str:
        """
        Proje adı ve UUID kullanılarak benzersiz rapor ID'si oluşturur
        
        Args:
            project_name: Proje adı
            
        Returns:
            Rapor ID'si (format: {Projeadi}_{UUID})
        """
        safe_project = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name)
        unique_id = str(uuid4())
        return f"{safe_project}_{unique_id}"


def sanitize_filename(name: str) -> str:
    """
    Dosya adını güvenli hale getirir.
    
    Args:
        name: Orijinal isim
        
    Returns:
        Güvenli dosya adı
    """
    # Türkçe karakterleri ve boşlukları düzelt
    name = name.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    name = name.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    
    # Sadece alfanumerik karakterler, tire ve alt çizgi
    return re.sub(r'[^a-zA-Z0-9\-_]', '_', name)

def ensure_report_directory(project_name: str) -> Path:
    """
    Proje raporları için dizin oluşturur ve yolunu döndürür.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Proje rapor dizininin yolu
    """
    safe_project_name = sanitize_filename(project_name)
    project_dir = BASE_REPORTS_DIR / safe_project_name
    
    if not project_dir.exists():
        project_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Proje rapor dizini oluşturuldu: {project_dir}")
    
    return project_dir

def ensure_active_report_structure(project_name: str) -> Path:
    """
    Aktif rapor işleme için gerekli dizin yapısını oluşturur ve proje yolunu döndürür.
    (backend/data/uploads/active_report/{proje_adı}/images ve text)

    Args:
        project_name: Proje adı

    Returns:
        Aktif rapor proje dizininin yolu (örn: backend/data/uploads/active_report/{proje_adı})
    """
    # Proje adını sanitize etmeye gerek yok, çünkü bu dizin adı API'den geliyor olabilir
    # ve orjinal haliyle kullanılması gerekebilir. Gerekirse burada da sanitize eklenebilir.
    project_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower()
    images_dir = project_dir / "images"
    text_dir = project_dir / "text"

    for dir_path in [project_dir, images_dir, text_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"[FILE] Aktif rapor dizini oluşturuldu: {dir_path}")
            
    return project_dir # Ana proje dizinini döndür

def clean_active_report_directory(project_name: str) -> bool:
    """
    Belirli bir proje için aktif rapor dizinini temizler (siler).
    
    Args:
        project_name: Temizlenecek proje adı
        
    Returns:
        bool: İşlem başarılıysa True, aksi halde False
    """
    try:
        project_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower()
        if not project_dir.exists():
            logger.warning(f"[CleanReport] Temizlenecek dizin bulunamadı: {project_dir}")
            return True # Dizin yoksa, zaten temizlenmiş sayılır
        
        shutil.rmtree(project_dir)
        logger.info(f"[CleanReport] Aktif rapor dizini temizlendi: {project_dir}")
        return True
    except Exception as e:
        logger.error(f"[CleanReport] Aktif rapor dizini temizlenirken hata: {str(e)}", exc_info=True)
        return False

def save_component_text(project_name: str, component_name: str, text_content: str) -> Tuple[bool, str]:
    """
    Bir projeye ait bileşenin metin içeriğini JSON dosyasına kaydeder.
    Dosya yoksa oluşturur, varsa günceller.

    Args:
        project_name: Proje adı
        component_name: Bileşen adı
        text_content: Kaydedilecek metin içeriği

    Returns:
        Tuple[bool, str]: (Başarı durumu, Hata mesajı (başarısızsa))
    """
    try:
        # Önce gerekli dizin yapısının var olduğundan emin ol
        project_dir = ensure_active_report_structure(project_name)
        components_file = project_dir / "text" / "components.json"
        
        components_data = {}
        # Eğer dosya varsa, mevcut içeriği oku
        if components_file.exists():
            try:
                with open(components_file, "r", encoding="utf-8") as f:
                    components_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"[SaveText] JSON dosyası okunamadı veya boş: {components_file}. Yeni dosya oluşturulacak.")
                # Hatalı veya boş dosyayı görmezden gel, üzerine yazılacak
                components_data = {}
            except Exception as read_err:
                logger.error(f"[SaveText] JSON okunurken beklenmedik hata: {components_file}, Hata: {read_err}", exc_info=True)
                return False, f"Mevcut JSON dosyası okunurken hata: {read_err}"

        # Yeni veriyi ekle veya güncelle
        components_data[component_name] = text_content
        
        # Güncellenmiş veriyi dosyaya yaz
        with open(components_file, "w", encoding="utf-8") as f:
            json.dump(components_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"[SaveText] Bileşen metni kaydedildi: {component_name} - Proje: {project_name}")
        return True, ""
        
    except Exception as e:
        logger.error(f"[SaveText] Bileşen metni kaydedilirken hata: {str(e)}", exc_info=True)
        return False, str(e)

def get_active_report_image_paths(project_name: str) -> List[str]:
    """
    Belirli bir projenin aktif rapor dizinindeki tüm görsellerin dosya yollarını döndürür.

    Args:
        project_name: Proje adı

    Returns:
        List[str]: Görsel dosyalarının string olarak yollarının listesi.
                   Dizin bulunamazsa veya hata olursa boş liste döner.
    """
    try:
        image_dir = BASE_ACTIVE_REPORT_DIR / project_name.lower() / "images"
        if not image_dir.exists() or not image_dir.is_dir():
            logger.warning(f"[GetImages] Görsel dizini bulunamadı veya bir dizin değil: {image_dir}")
            return []

        # Yaygın görsel uzantıları
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff')

        image_paths = []
        for file in image_dir.glob("*"):
            # Dosya olduğundan ve geçerli bir uzantıya sahip olduğundan emin ol
            if file.is_file() and file.suffix.lower() in image_extensions:
                image_paths.append(str(file))

        logger.info(f"[GetImages] {len(image_paths)} adet görsel bulundu: Proje {project_name}")
        return image_paths

    except Exception as e:
        logger.error(f"[GetImages] Görseller alınırken hata: Proje {project_name}, Hata: {str(e)}", exc_info=True)
        return [] # Hata durumunda boş liste döndür

def generate_report_filename(project_name: str, report_id: str) -> str:
    """
    Standart rapor dosya adı oluşturur.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Oluşturulan dosya adı
    """
    return f"{report_id}.pdf"

def get_report_path(project_name: str, report_id: str) -> Path:
    """
    Rapor dosyasının tam yolunu oluşturur.
    
    Args:
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Rapor dosyasının tam yolu
    """
    project_dir = ensure_report_directory(project_name)
    filename = generate_report_filename(project_name, report_id)
    return project_dir / filename

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    PDF dosyasından metin içeriğini çıkarır.
    
    Args:
        filepath: PDF dosyasının yolu
        
    Returns:
        str: PDF'ten çıkarılan metin, hata durumunda None
    """
    try:
        # PDF dosyasını kontrol et
        if not os.path.exists(filepath):
            logger.error(f"PDF dosyası bulunamadı: {filepath}")
            return None
            
        # PDF'ten metin çıkar
        with pdfplumber.open(filepath) as pdf:
            text_content = ""
            
            # Tüm sayfalardan metin çıkar
            for page in pdf.pages:
                extracted_text = page.extract_text() or ""
                text_content += extracted_text + "\n"
                
            return text_content.strip()
    except Exception as e:
        logger.error(f"PDF işleme hatası: {str(e)}")
        return None

def save_pdf_content(content: bytes, project_name: str, report_id: str) -> Tuple[Path, bool]:
    """
    PDF içeriğini dosyaya kaydeder.
    
    Args:
        content: PDF içeriği (bytes)
        project_name: Proje adı
        report_id: Rapor ID
        
    Returns:
        Tuple[Path, bool]: (Dosya yolu, başarı durumu)
    """
    try:
        pdf_path = get_report_path(project_name, report_id)
        
        # PDF içeriğini kaydet
        with open(pdf_path, 'wb') as f:
            f.write(content)
            
        logger.info(f"PDF başarıyla kaydedildi: {pdf_path}")
        return pdf_path, True
        
    except Exception as e:
        logger.error(f"PDF kaydedilirken hata: {str(e)}")
        return Path(), False

def get_pdf_info(pdf_path: Path) -> Optional[dict]:
    """
    PDF dosyası hakkında temel bilgileri döndürür.
    
    Args:
        pdf_path: PDF dosyasının yolu
        
    Returns:
        dict: PDF bilgileri veya None
    """
    try:
        if not pdf_path.exists():
            logger.error(f"PDF dosyası bulunamadı: {pdf_path}")
            return None
            
        file_size = pdf_path.stat().st_size
        created_time = datetime.fromtimestamp(pdf_path.stat().st_ctime)
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
        return {
            "file_path": str(pdf_path),
            "file_size": file_size,
            "created_at": created_time.isoformat(),
            "page_count": page_count
        }
        
    except Exception as e:
        logger.error(f"PDF bilgileri alınırken hata: {str(e)}")
        return None 
    # Add this function to your existing pdf_utils.py file

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_path: Path) -> Optional[str]:
    """
    Encode an image file to base64 data URI.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 data URI string or None if error
    """
    try:
        # Determine MIME type based on file extension
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff'
        }
        
        suffix = image_path.suffix.lower()
        mime_type = mime_types.get(suffix, 'image/jpeg')
        
        # Read and encode the image
        with open(image_path, 'rb') as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
            
        return f"data:{mime_type};base64,{encoded}"
        
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {str(e)}")
        return None

def get_project_images_map(project_name: str) -> Dict[str, str]:
    """
    Create a mapping of image filenames to their base64 data URIs.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dictionary mapping filenames to base64 data URIs
    """
    from pathlib import Path
    
    # Define paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    ACTIVE_UPLOADS_PATH = BASE_DIR / "data" / "uploads" / "active_report"
    
    # Create slug from project name (matching the pattern in your code)
    slug = project_name.lower().replace(" ", "_")
    image_folder = ACTIVE_UPLOADS_PATH / slug / "images"
    
    images_map = {}
    
    if not image_folder.exists():
        logger.warning(f"Image folder not found: {image_folder}")
        return images_map
    
    # Process all images in the folder
    for image_path in image_folder.glob("*"):
        if image_path.is_file() and image_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff']:
            filename = image_path.name
            base64_data = encode_image_to_base64(image_path)
            
            if base64_data:
                images_map[filename] = base64_data
                logger.info(f"Encoded image: {filename}")
            else:
                logger.warning(f"Failed to encode image: {filename}")
    
    return images_map

def load_project_assets(project_name: str) -> Dict[str, str]:
    """
    Load project assets (logo, banner) and convert them to base64.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dictionary mapping asset names to base64 data URIs
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    assets_map = {}
    
    # Try to load from project_assets directory
    project_slug = project_name.lower().replace(" ", "_")
    assets_dir = BASE_DIR / "data" / "project_assets" / project_slug
    
    if assets_dir.exists():
        for asset_path in assets_dir.glob("*"):
            if asset_path.is_file() and asset_path.suffix.lower() in ['.svg', '.png', '.jpg', '.jpeg']:
                asset_name = asset_path.stem  # Get filename without extension
                base64_data = encode_image_to_base64(asset_path)
                if base64_data:
                    assets_map[asset_name] = base64_data
                    logger.info(f"Loaded project asset: {asset_name}")
    
    # Also check for common assets in the parent project_assets directory
    common_assets_dir = BASE_DIR / "data" / "project_assets"
    for asset_name in ['isra_logo', 'logo']:
        for ext in ['.png', '.svg', '.jpg']:
            asset_path = common_assets_dir / f"{asset_name}{ext}"
            if asset_path.exists():
                base64_data = encode_image_to_base64(asset_path)
                if base64_data:
                    assets_map[asset_name] = base64_data
                    logger.info(f"Loaded common asset: {asset_name}")
                break
    
    return assets_map

def replace_image_placeholders_in_html(html_content: str, project_name: str) -> str:
    """
    Replace image filename placeholders and template variables in HTML with base64 encoded images.
    
    This function:
    1. Replaces {{project_slug}} template variables
    2. Replaces image filenames with base64 data URIs
    3. Handles project assets (logo, banner)
    4. Removes external stylesheet references
    
    Args:
        html_content: The HTML content with placeholders
        project_name: Name of the project
        
    Returns:
        HTML content with images replaced by base64 data URIs
    """
    # First, replace template variables
    project_slug = project_name.lower().replace(" ", "_")
    html_content = html_content.replace("{{project_slug}}", project_slug)
    
    # Remove external stylesheet references as they cause issues with WeasyPrint
    html_content = re.sub(r'<link\s+[^>]*href\s*=\s*["\']assets/styles\.css["\'][^>]*>', '', html_content)
    
    # Get uploaded images map
    images_map = get_project_images_map(project_name)
    
    # Get project assets map
    assets_map = load_project_assets(project_name)
    
    # Combine both maps
    all_images = {**images_map, **assets_map}
    
    if not all_images:
        logger.warning(f"No images or assets found for project: {project_name}")
    
    # Pattern to match img tags with src attributes
    img_pattern = r'<img\s+([^>]*\s+)?src\s*=\s*["\']([^"\']+)["\']([^>]*)>'
    
    def replace_img_src(match):
        """Replace function for regex substitution."""
        before_src = match.group(1) or ''
        src_value = match.group(2)
        after_src = match.group(3) or ''
        
        # Extract just the filename from various path formats
        filename = None
        if 'project_assets/' in src_value:
            # Handle project_assets/v_metroway/logo.svg format
            parts = src_value.split('/')
            if len(parts) >= 2:
                filename = parts[-1].split('.')[0]  # Get filename without extension
        elif '/' not in src_value and '\\' not in src_value and not src_value.startswith(('http://', 'https://', 'data:')):
            # It's already just a filename
            filename = src_value
        
        if filename:
            # Try to find the image in our maps
            # First try with extension
            if filename in all_images:
                logger.info(f"Replacing image placeholder: {filename}")
                return f'<img {before_src}src="{all_images[filename]}"{after_src}>'
            # Then try without extension
            filename_no_ext = filename.split('.')[0]
            if filename_no_ext in all_images:
                logger.info(f"Replacing image placeholder: {filename_no_ext}")
                return f'<img {before_src}src="{all_images[filename_no_ext]}"{after_src}>'
            else:
                logger.warning(f"Image not found: {filename}")
        
        # Return original if no replacement needed
        return match.group(0)
    
    # Replace all img tags
    modified_html = re.sub(img_pattern, replace_img_src, html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Handle CSS background-image properties
    css_pattern = r'background:\s*url\(["\']?([^"\')]+)["\']?\)([^;]*);'
    
    def replace_css_url(match):
        """Replace function for CSS background images."""
        url_value = match.group(1)
        css_props = match.group(2)
        
        # Extract filename from path
        if 'project_assets/' in url_value:
            parts = url_value.split('/')
            if len(parts) >= 2:
                filename = parts[-1].split('.')[0]
                if filename in all_images:
                    logger.info(f"Replacing CSS background image: {filename}")
                    return f'background: url("{all_images[filename]}"){css_props};'
        
        return match.group(0)
    
    # Replace CSS background images
    modified_html = re.sub(css_pattern, replace_css_url, modified_html, flags=re.IGNORECASE)
    
    return modified_html

# Example of how to integrate this into your existing generate_pdf_from_html function:
def generate_pdf_from_html_with_images(html_content: str, project_name: str, report_id: str) -> Path:
    """
    Enhanced version of generate_pdf_from_html that replaces image placeholders.
    
    Args:
        html_content: The HTML content with image placeholders
        project_name: The name of the project
        report_id: The unique report ID
        
    Returns:
        Path: The path to the generated PDF file
    """
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    
    logger = logging.getLogger(__name__)
    
    # First, replace image placeholders with base64 data
    html_with_images = replace_image_placeholders_in_html(html_content, project_name)
    
    # Wrap the HTML content in a complete document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{project_name} - Yatırımcı Raporu</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
                margin-top: 1.5em;
            }}
            h1 {{
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 0.5em;
            }}
            section {{
                margin-bottom: 2em;
                page-break-inside: avoid;
            }}
            figure {{
                margin: 1em 0;
                text-align: center;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            figcaption {{
                font-style: italic;
                color: #666;
                margin-top: 0.5em;
            }}
            .logo {{
                height: 42px;
            }}
            .banner {{
                height: 80px;
                background-color: #f0f0f0;
                margin-bottom: 2em;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        {html_with_images}
    </body>
    </html>
    """
    
    # Get the PDF output path
    pdf_path = get_report_path(project_name, report_id)
    
    # Ensure the directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"[PDF] Generating PDF at: {pdf_path}")
    
    try:
        # Configure fonts
        font_config = FontConfiguration()
        
        # Create PDF from HTML
        HTML(string=full_html).write_pdf(str(pdf_path), font_config=font_config)
        
        logger.info(f"[PDF] PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"[PDF] Error generating PDF: {str(e)}")
        raise Exception(f"Failed to generate PDF: {str(e)}")