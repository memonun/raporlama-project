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
from playwright.async_api import async_playwright
import asyncio

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
    Load project assets (SVGs, logos) and convert them to base64.
    Uses the manifest.json to know which assets to load.
    """
    from pathlib import Path
    import json
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    assets_map = {}
    
    # Load manifest to know which assets belong to this project
    manifest_path = BASE_DIR / "data" / "project_assets" / "manifest.json"
    if not manifest_path.exists():
        logger.warning(f"Manifest file not found: {manifest_path}")
        return assets_map
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        logger.error(f"Error loading manifest: {e}")
        return assets_map
    
    # Check if project has assets defined
    if project_name not in manifest:
        logger.warning(f"No assets defined for project: {project_name}")
        return assets_map
    
    project_assets = manifest[project_name]
    
    # Load each asset defined in manifest
    for asset_name, asset_path in project_assets.items():
        # Convert relative path to absolute
        if asset_path.startswith("backend/"):
            asset_path = asset_path.replace("backend/", "")
        
        full_path = BASE_DIR / asset_path
        
        if full_path.exists():
            base64_data = encode_image_to_base64(full_path)
            if base64_data:
                # Use the asset name from manifest as the key
                assets_map[asset_name] = base64_data
                logger.info(f"Loaded project asset: {asset_name} from {full_path}")
        else:
            logger.warning(f"Asset file not found: {full_path}")
    
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
# def generate_pdf_from_html_with_images(html_content: str, project_name: str, report_id: str) -> Path:
#     """
#     Enhanced version that better handles SVG and image replacement for WeasyPrint.
#     """
#     from weasyprint import HTML, CSS
#     from weasyprint.text.fonts import FontConfiguration
#     import re
    
#     logger.info(f"[PDF] Starting PDF generation for project: {project_name}")
    
#     # Get all available images and assets
#     images_map = get_project_images_map(project_name)
#     assets_map = load_project_assets(project_name)
#     all_images = {**images_map, **assets_map}
    
#     logger.info(f"[PDF] Available assets: {list(all_images.keys())}")
    
#     # Enhanced replacement function that handles img tags
#     def replace_all_image_references(html: str) -> str:
#         """Replace all image references with base64 data URIs"""
        
#         # Pattern for img src attributes
#         img_pattern = r'<img\s+([^>]*?)src\s*=\s*["\']?([^"\'\s>]+)["\']?([^>]*?)>'
        
#         def replace_img(match):
#             before = match.group(1) or ''
#             src = match.group(2)
#             after = match.group(3) or ''
            
#             # Clean the src to get just the filename
#             filename = src.split('/')[-1].split('.')[0]
            
#             if filename in all_images:
#                 logger.info(f"[PDF] Replacing image: {filename}")
#                 return f'<img {before}src="{all_images[filename]}"{after}>'
#             else:
#                 logger.warning(f"[PDF] Image not found: {filename} (from src: {src})")
#                 # Try to find a close match
#                 for key in all_images.keys():
#                     if key.lower() in filename.lower() or filename.lower() in key.lower():
#                         logger.info(f"[PDF] Using close match: {key} for {filename}")
#                         return f'<img {before}src="{all_images[key]}"{after}>'
#                 return match.group(0)
        
#         html = re.sub(img_pattern, replace_img, html, flags=re.IGNORECASE | re.DOTALL)
        
#         return html
    
#     # Replace all image references
#     html_with_images = replace_all_image_references(html_content)
    
#     # Additional CSS for better PDF rendering
#     additional_css = """
#     <style>
#         /* Ensure images don't break across pages */
#         img { 
#             page-break-inside: avoid; 
#             max-width: 100%;
#             height: auto;
#         }
#         .page { 
#             page-break-after: always;
#             page-break-inside: avoid;
#         }
#         /* Better print rendering */
#         @media print {
#             .page {
#                 margin: 0;
#                 padding: 0;
#             }
#         }
#     </style>
#     """
    
#     # Insert additional CSS before closing head tag
#     if '</head>' in html_with_images:
#         html_with_images = html_with_images.replace('</head>', additional_css + '</head>')
    
#     # Save debug HTML
#     debug_path = Path(f"debug_{project_name}_final.html")
#     with open(debug_path, 'w', encoding='utf-8') as f:
#         f.write(html_with_images)
#     logger.info(f"[PDF] Debug HTML saved to: {debug_path}")
    
#     # Get PDF output path
#     pdf_path = get_report_path(project_name, report_id)
#     pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
#     try:
#         # Configure fonts
#         font_config = FontConfiguration()
        
#         # Create PDF with specific options for better rendering
#         HTML(
#             string=html_with_images,
#             base_url=str(Path(__file__).parent.parent)
#         ).write_pdf(
#             str(pdf_path),
#             font_config=font_config,
#             presentational_hints=True,  # Better CSS support
#             optimize_images=True,       # Optimize embedded images
#         )
        
#         logger.info(f"[PDF] PDF generated successfully: {pdf_path}")
#         return pdf_path
        
#     except Exception as e:
#         logger.error(f"[PDF] Error generating PDF: {str(e)}", exc_info=True)
#         raise Exception(f"Failed to generate PDF: {str(e)}")

def replace_image_placeholders_in_html(html_content: str, project_name: str) -> str:
    """
    Replace image filename placeholders in HTML with base64 encoded images.
    Handles both img src and CSS background-image properties.
    """
    import re
    from pathlib import Path
    
    # Get uploaded images map
    images_map = get_project_images_map(project_name)
    
    # Get project assets map (SVGs)
    assets_map = load_project_assets(project_name)
    
    # Combine both maps
    all_images = {**images_map, **assets_map}
    
    logger.info(f"[Replace] Available images for {project_name}: {list(all_images.keys())}")
    
    if not all_images:
        logger.warning(f"No images or assets found for project: {project_name}")
        return html_content
    
    # Pattern 1: Replace img src attributes (with or without quotes)
    img_pattern = r'<img\s+([^>]*\s+)?src\s*=\s*["\']?([^"\'\s>]+)["\']?([^>]*)>'
    
    def replace_img_src(match):
        before_src = match.group(1) or ''
        src_value = match.group(2)
        after_src = match.group(3) or ''
        
        # Clean the src value (remove any paths, extensions)
        filename = src_value.split('/')[-1].split('.')[0]
        
        if filename in all_images:
            logger.info(f"[Replace] Replacing img src: {filename}")
            return f'<img {before_src}src="{all_images[filename]}"{after_src}>'
        else:
            logger.warning(f"[Replace] Image not found in assets: {filename}")
            return match.group(0)
    
    # Replace all img tags
    html_content = re.sub(img_pattern, replace_img_src, html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Pattern 2: Replace CSS background-image in style attributes
    # Match both url('filename') and url(filename) formats
    style_bg_pattern = r'style\s*=\s*["\']([^"\']*background-image:\s*url\(["\']?)([^"\'\)]+)(["\']?\)[^"\']*)["\']'
    
    def replace_style_bg(match):
        style_before = match.group(1)
        url_value = match.group(2)
        style_after = match.group(3)
        
        # Clean the filename
        filename = url_value.split('/')[-1].split('.')[0]
        
        if filename in all_images:
            logger.info(f"[Replace] Replacing background-image: {filename}")
            return f'style="{style_before}{all_images[filename]}{style_after}"'
        else:
            logger.warning(f"[Replace] Background image not found: {filename}")
            return match.group(0)
    
    # Replace background-image in style attributes
    html_content = re.sub(style_bg_pattern, replace_style_bg, html_content, flags=re.IGNORECASE)
    
    # Pattern 3: Replace background: url() in CSS styles
    css_bg_pattern = r'background:\s*url\(["\']?([^"\'\)]+)["\']?\)([^;}]*)'
    
    def replace_css_bg(match):
        url_value = match.group(1)
        css_props = match.group(2)
        
        # Clean the filename
        filename = url_value.split('/')[-1].split('.')[0]
        
        if filename in all_images:
            logger.info(f"[Replace] Replacing CSS background: {filename}")
            return f'background: url("{all_images[filename]}"){css_props}'
        else:
            logger.warning(f"[Replace] CSS background image not found: {filename}")
            return match.group(0)
    
    # Replace CSS background
    html_content = re.sub(css_bg_pattern, replace_css_bg, html_content, flags=re.IGNORECASE)
    
    # Pattern 4: Handle any remaining url() references in the CSS
    remaining_url_pattern = r'url\(["\']?([^"\'\)]+)["\']?\)'
    
    def replace_remaining_urls(match):
        url_value = match.group(1)
        
        # Skip if it's already a data URI
        if url_value.startswith('data:'):
            return match.group(0)
            
        # Clean the filename
        filename = url_value.split('/')[-1].split('.')[0]
        
        if filename in all_images:
            logger.info(f"[Replace] Replacing remaining URL: {filename}")
            return f'url("{all_images[filename]}")'
        else:
            return match.group(0)
    
    # Replace remaining URLs
    html_content = re.sub(remaining_url_pattern, replace_remaining_urls, html_content, flags=re.IGNORECASE)
    
    return html_content    
    

def debug_html_content(html_content: str, project_name: str):
    """
    Debug function to log all image/SVG references in the HTML
    """
    import re
    
    logger.info(f"[DEBUG] Analyzing HTML for project: {project_name}")
    
    # Find all img src references
    img_srcs = re.findall(r'<img[^>]+src\s*=\s*["\']?([^"\'\s>]+)', html_content, re.IGNORECASE)
    logger.info(f"[DEBUG] Found img src values: {img_srcs}")
    
    # Find all background-image references
    bg_images = re.findall(r'background-image:\s*url\(["\']?([^"\'\)]+)', html_content, re.IGNORECASE)
    logger.info(f"[DEBUG] Found background-image values: {bg_images}")
    
    # Find all background url references
    bg_urls = re.findall(r'background:\s*url\(["\']?([^"\'\)]+)', html_content, re.IGNORECASE)
    logger.info(f"[DEBUG] Found background url values: {bg_urls}")
    
    # Check what assets are available
    assets_map = load_project_assets(project_name)
    logger.info(f"[DEBUG] Available assets: {list(assets_map.keys())}")
    
    return    

logger = logging.getLogger(__name__)

async def generate_pdf_with_playwright(html_content: str, project_name: str, report_id: str) -> Path:
    """
    Generate PDF using Playwright with async API.
    This will render the HTML exactly as a browser would see it.
    """
    logger.info(f"[PDF] Starting Playwright PDF generation for project: {project_name}")
    
    # Get all available images and assets
    images_map = get_project_images_map(project_name)
    assets_map = load_project_assets(project_name)
    all_images = {**images_map, **assets_map}
    
    # Function to replace image references with base64
    def replace_image_references(html: str) -> str:
        # Handle img src
        img_pattern = r'<img\s+([^>]*?)src\s*=\s*["\']?([^"\'\s>]+)["\']?([^>]*?)>'
        
        def replace_img(match):
            before = match.group(1) or ''
            src = match.group(2)
            after = match.group(3) or ''
            
            # Clean the src to get just the filename
            filename = src.split('/')[-1].split('.')[0]
            
            # Try to find the image with various normalizations
            for key in all_images.keys():
                if (key == filename or 
                    key.split('.')[0] == filename or
                    key.lower() == filename.lower() or
                    key.replace('İ', 'I').replace('ı', 'i').replace('ş', 's').replace('ğ', 'g') == filename):
                    logger.info(f"[PDF] Replacing image: {filename} -> {key}")
                    return f'<img {before}src="{all_images[key]}"{after}>'
            
            logger.warning(f"[PDF] Image not found: {filename}")
            return match.group(0)
        
        html = re.sub(img_pattern, replace_img, html, flags=re.IGNORECASE | re.DOTALL)
        
        # Handle CSS background-image
        bg_pattern = r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
        
        def replace_bg(match):
            bg_url = match.group(1)
            filename = bg_url.split('/')[-1].split('.')[0]
            
            for key in all_images.keys():
                if (key == filename or 
                    key.split('.')[0] == filename or
                    key.lower() == filename.lower()):
                    logger.info(f"[PDF] Replacing background: {filename} -> {key}")
                    return f'background-image: url({all_images[key]})'
            
            logger.warning(f"[PDF] Background image not found: {filename}")
            return match.group(0)
        
        html = re.sub(bg_pattern, replace_bg, html, flags=re.IGNORECASE)
        
        return html
    
    # Replace all image references with base64
    html_with_images = replace_image_references(html_content)
    
    # Save debug HTML
    debug_path = Path(f"debug_{project_name}_playwright.html")
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(html_with_images)
    logger.info(f"[PDF] Debug HTML saved to: {debug_path}")
    
    # Generate PDF with Playwright
    pdf_path = get_report_path(project_name, report_id)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage']  # Helps with Docker/limited memory
        )
        
        try:
            # Create page
            page = await browser.new_page()
            
            # Set viewport to A4 size
            await page.set_viewport_size({"width": 794, "height": 1123})
            
            # Load the HTML content
            await page.set_content(html_with_images, wait_until='networkidle')
            
            # Wait a bit for any async rendering
            await page.wait_for_timeout(1000)
            
            # Generate PDF
            await page.pdf(
                path=str(pdf_path),
                format='A4',
                print_background=True,
                margin={
                    'top': '0',
                    'right': '0',
                    'bottom': '0',
                    'left': '0'
                },
                prefer_css_page_size=True
            )
            
            logger.info(f"[PDF] PDF generated successfully: {pdf_path}")
            
        finally:
            await browser.close()
    
    return pdf_path


# Alternative: If your main function is sync, create a wrapper
def generate_pdf_from_html_with_images(html_content: str, project_name: str, report_id: str) -> Path:
    """
    Sync wrapper for async Playwright PDF generation.
    Use this if your calling code is synchronous.
    """
    # Check if we're already in an event loop
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a new task
        future = asyncio.create_task(
            generate_pdf_with_playwright(html_content, project_name, report_id)
        )
        # This won't work in an already running loop, so we need a different approach
        # The calling code should be async instead
        raise RuntimeError(
            "Cannot use sync wrapper in async context. "
            "Please use 'await generate_pdf_with_playwright()' directly."
        )
    except RuntimeError:
        # No event loop, we can create one
        return asyncio.run(
            generate_pdf_with_playwright(html_content, project_name, report_id)
        )