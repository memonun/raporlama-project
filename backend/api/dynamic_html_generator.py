import os
import json
import logging
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import PROJECT_PALETTES, CORPORATE_COLORS

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_project_style_config(project_name: str) -> Dict[str, Any]:
    """
    Bir proje için stil yapılandırmasını alır: renk paleti, font bilgileri vb.
    """
    project_name = project_name.lower()
    
    # Proje için renk paleti
    project_colors = PROJECT_PALETTES.get(project_name, {})
    if not project_colors:
        logger.warning(f"[HTML_GEN] Proje için ({project_name}) renk paleti bulunamadı. Varsayılan renkler kullanılacak.")
        # Varsayılan renk paleti
        project_colors = {
            'primary': '#3366CC',
            'secondary': '#6699FF',
            'accent': '#FF9900',
            'background': '#F5F7FA',
            'text': '#333333',
        }
    
    # Font bilgileri
    # 1. Projeye özel font yolu kontrolü
    font_dir = Path(__file__).parent.parent / 'static' / 'assets' / 'fonts'
    project_font_path = font_dir / "gothamrnd_light.ttf"
    project_font = None
    
    # Projeye özel bir font varsa
    if project_font_path.exists():
        project_font = project_font_path.name
    else:
        # Varsayılan font - Montserrat
        default_font_path = font_dir / "Montserrat-VariableFont_wght.ttf"
        if default_font_path.exists():
            project_font = default_font_path.name
        else:
            # Herhangi bir font varsa
            available_fonts = list(font_dir.glob('*.ttf'))
            if available_fonts:
                project_font = available_fonts[0].name
    
    # Şirket renkleri
    corporate_colors = CORPORATE_COLORS.copy()
    
    # Sonuç stil yapılandırması
    style_config = {
        'colors': project_colors,
        'corporate_colors': corporate_colors,
        'font': project_font,
        'layout': 'standard',  # veya 'modern', 'classic' gibi farklı düzenler eklenebilir
    }
    
    return style_config

def process_images_for_report(project_name: str, image_paths: List[str]) -> List[Dict[str, str]]:
    """
    Resimleri rapor için işler ve URL veya base64 formatına dönüştürür
    """
    processed_images = []
    
    for image_path in image_paths:
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"[HTML_GEN] Görsel bulunamadı: {image_path}")
            continue
        
        # Dosya adı ve uzantısını al
        file_name = os.path.basename(image_path)
        _, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()
        
        # MIME tipi belirle
        mime_type = None
        if file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.svg':
            mime_type = 'image/svg+xml'
        elif file_ext == '.gif':
            mime_type = 'image/gif'
        else:
            mime_type = 'image/jpeg'  # Varsayılan
        
        try:
            # Görsel datası
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
            # Base64 URL oluştur
            data_url = f"data:{mime_type};base64,{img_data}"
            
            # Bazı meta verilerle birlikte ekle
            processed_images.append({
                'src': data_url,
                'name': file_name,
                'type': mime_type,
                'alt': f"{project_name} - {file_name}"
            })
            
            logger.info(f"[HTML_GEN] Görsel işlendi: {file_name}")
            
        except Exception as e:
            logger.error(f"[HTML_GEN] Görsel işlenirken hata: {file_name} - {str(e)}")
    
    return processed_images

def generate_dynamic_html(project_name: str, components_data: Dict[str, Any],  style_config: Dict[str, Any], image_urls: List[Dict[str, str]],svg_backgrounds: Dict[str, str] = None) -> str:
    """
    GPT ile dinamik HTML içeriği oluşturur.
    
    Parameters:
    -----------
    project_name : str
        Proje adı
    components_data : Dict[str, Any]
        Her bileşen için içerik verileri
    style_config : Dict[str, Any]
        Proje stil yapılandırması
    image_urls : List[Dict[str, str]]
        İşlenmiş görseller listesi
    svg_backgrounds : Dict[str, str], optional
        SVG arkaplan görsellerinin ve logonun data URI'leri
    
    Returns:
    --------
    str
        Oluşturulan HTML içeriği
    """
    from api.gpt_handler import query_gpt  # Döngüsel bağımlılığı önlemek için burada import ediyoruz
    
    logger.info(f"[HTML_GEN] Dinamik HTML oluşturma başlatıldı: Proje={project_name}")
    
    # SVG arkaplanları hazırla
    if svg_backgrounds is None:
        svg_backgrounds = {}
    
    logo_uri = svg_backgrounds.get('logo', '')
    general_bg_uri = svg_backgrounds.get('general_bg', '')
    cover_bg_uri = svg_backgrounds.get('cover_bg', '')
    
    # Tüm görselleri log'a yazdır (Debug)
    for img in image_urls:
        logger.info(f"[HTML_GEN] Kullanılabilir görsel: {img['name']}")
    
    # SVG arkaplanlarını log'a yazdır
    for key, value in svg_backgrounds.items():
        if value:
            logger.info(f"[HTML_GEN] SVG arkaplan mevcut: {key}")
    
    # AI için dönüştürülecek veri hazırlığı
    # Görsel URL'lerini işle ve metin içeriğiyle eşleştir
    components_with_images = {}
    for component_name, component_data in components_data.items():
        if 'answers' in component_data:
            # Bir bileşene ait tüm metinleri birleştir
            combined_text = ""
            for key, value in component_data['answers'].items():
                if (not key.endswith('_image_0') and not key.endswith('_content') and 
                    not key.endswith('.jpg') and not key.endswith('.png') and 
                    not key.endswith('.svg')):
                    # JSON formatında olabilecek verileri kontrol et ve ayıkla
                    if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                        try:
                            json_data = json.loads(value)
                            if 'content' in json_data:
                                combined_text += json_data['content'] + "\n\n"
                            else:
                                combined_text += value + "\n\n"
                        except json.JSONDecodeError:
                            combined_text += value + "\n\n"
                    else:
                        combined_text += str(value) + "\n\n"
                        
            # Bu bileşene ait görselleri bul (daha gelişmiş eşleştirme mantığı)
            component_name_lower = component_name.lower().replace(" ", "_").replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ç", "c").replace("ö", "o")
            
            # Görselleri birden fazla şekilde eşleştirmeyi dene
            component_images = []
            
            # 1. Tam isim eşleşmesi (component_name-X.jpg)
            component_images.extend([img for img in image_urls 
                                  if img['name'].lower().startswith(f"{component_name_lower}-")])
            
            # 2. Kısmi isim eşleşmesi (bir dosya adı component adını içeriyorsa)
            if not component_images:
                component_images.extend([img for img in image_urls 
                                     if component_name_lower in img['name'].lower()])
            
            # 3. En son çare: semantik eşleştirme (bazı semantik kelimelere bakalım)
            if not component_images and component_name_lower in ['finans', 'mali', 'finansal']:
                component_images.extend([img for img in image_urls 
                                     if any(keyword in img['name'].lower() for keyword in 
                                           ['finans', 'para', 'ekonomi', 'mali', 'gelir', 'gider', 'bütçe'])])
            
            if not component_images and component_name_lower in ['inşaat', 'yapı', 'yapi', 'insaat']:
                component_images.extend([img for img in image_urls 
                                     if any(keyword in img['name'].lower() for keyword in 
                                           ['inşaat', 'yapı', 'bina', 'proje', 'şantiye', 'santiye'])])
            
            # Eşleşen görselleri loglama
            logger.info(f"[HTML_GEN] Bileşen '{component_name}' için {len(component_images)} görsel bulundu.")
            
            components_with_images[component_name] = {
                'text': combined_text.strip(),
                'images': component_images
            }
    
    # GPT'ye gönderilecek istek formatını oluştur
    gpt_prompt = f"""
    # Yatırımcı Raporu HTML Oluşturma Görevi

    ## Genel Bilgiler
    - Proje: {project_name}
    - Stil: {json.dumps(style_config, indent=2, ensure_ascii=False)}
    
    ## Görev Tanımı 
    Aşağıdaki bileşen metinlerini ve görselleri kullanarak, belirlenen stilde estetik ve profesyonel bir HTML raporu oluştur. 
    
    ## SVG Arkaplanlar ve Logo
    Aşağıdaki özel görsel varlıkları HTML'de kullanmalısın:
    """
    
    if logo_uri:
        gpt_prompt += f"""
    - Logo: Bu logo her sayfada yer almalıdır. 
      URI: {logo_uri}
      Aşağıdaki HTML ile kullanabilirsin:
      ```html
      <img src="{logo_uri}" alt="İsra Holding Logo" class="logo" style="max-width: 180px; height: auto;">
      ```
    """
    
    if cover_bg_uri:
        gpt_prompt += f"""
    - Kapak Sayfası Arkaplanı: İlk sayfada (kapakta) arkaplan olarak kullanılmalıdır.
      URI: {cover_bg_uri}
      Aşağıdaki CSS ile kullanabilirsin:
      ```html
      <div class="cover-page" style="background-image: url('{cover_bg_uri}'); background-size: cover; background-position: center; background-repeat: no-repeat; position: relative;">
        <!-- Kapak içeriği buraya -->
      </div>
      ```
    """
    
    if general_bg_uri:
        gpt_prompt += f"""
    - Genel Arkaplan: Tüm sayfalarda watermark/filigran olarak kullanılmalıdır.
      URI: {general_bg_uri}
      Aşağıdaki CSS ile kullanabilirsin:
      ```html
      <div class="content-with-bg" style="position: relative;">
        <div class="background-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: url('{general_bg_uri}'); background-size: contain; background-position: center; background-repeat: no-repeat; opacity: 0.1; z-index: -1;"></div>
        <!-- İçerik buraya -->
      </div>
      ```
    """
    
    gpt_prompt += """
    ## ÖNEMLİ!!! 
    Tüm görseller mutlaka rapora dahil edilmelidir. Her görsel için aşağıdaki HTML yapısını kullanmalısın:
    
    ```html
    <figure class="report-image">
      <img src="GÖRSEL_URL" alt="GÖRSEL_ALT_METNİ" class="img-fluid">
      <figcaption>BILEŞEN_ADI - Görsel</figcaption>
    </figure>
    ```
    
    Her bir figcaption, o görselin hangi bileşene ait olduğunu göstermelidir. Görseller mutlaka ilgili bileşen metninin içinde, uygun yerlerde konumlandırılmalıdır.
    
    Özellikler:
    - Her bileşen için ayrı bir section kullan ve HTML5 semantik etiketlerini doğru şekilde yerleştir (section, article, header, etc.)
    - Stil bilgilerini (renkler, fontlar) uygun HTML yapısına entegre et
    - ŞU ÇOK ÖNEMLİ: Her bileşen için verilen TÜM görselleri kullan ve görsel yerleşimlerini içerik akışına uygun olarak optimize et
    - Düzgün spacing, grid veya flexbox kullanımı ile resimler ve metin arasında dengeli bir yerleşim sağla
    - İçeriği okunabilir ve profesyonel bir şekilde sunarak, uygun başlık hiyerarşisi kullan

    ## Bileşen İçerikleri
    """
    
    gpt_prompt += json.dumps(components_with_images, indent=2, ensure_ascii=False)
    
    gpt_prompt += """

    ## Çıktı Formatı
    Sadece oluşturduğun HTML kodunu döndür, herhangi bir açıklama veya başka metin ekleme.
    Stil bilgilerini inline CSS (style="...") olarak ekle.
    
    ## SON KONTROL
    Kodunu oluşturmadan önce şu kontrolleri yap:
    1. Verilen TÜM görselleri kullandın mı? Her bileşen için resimler düzgün konumlandırıldı mı?
    2. Tüm img etiketlerinde src özelliği doğru şekilde ayarlandı mı?
    3. Figure ve figcaption kullanarak görselleri düzgün şekilde belirttiniz mi?
    4. Logo ve SVG arkaplanları belirtilen şekilde ekledin mi?
    
    Görsellerin HTML içinde düzgün gösterildiğinden ve BASE64 URL'lerinin doğru şekilde kullanıldığından emin ol.
    """
    
    try:
        # GPT'den HTML içeriği oluştur
        html_response = query_gpt(gpt_prompt, max_tokens=4000)
        
        # Sonucu temizle: sadece HTML içeriğini al
        html_content = html_response.strip()
        
        # HTML etiketlerini içerip içermediğini kontrol et
        if not html_content.startswith('<') or not html_content.endswith('>'):
            logger.warning(f"[HTML_GEN] GPT yanıtı HTML içermiyor. Temel HTML yapısına dönüştürülüyor.")
            html_content = f"""
            <div class="report-container">
                <h1 class="report-title">{project_name}</h1>
                {html_content}
            </div>
            """
        
        # Sağlama: Görseller doğru şekilde eklendi mi kontrol et
        img_tags_count = html_content.count('<img')
        img_data_urls_count = html_content.count('data:image/')
        
        logger.info(f"[HTML_GEN] Oluşturulan HTML'de {img_tags_count} adet <img> etiketi ve {img_data_urls_count} adet data:image/ URL'si var.")
        
        # Tüm görsellerin kullanıldığından emin ol
        for img in image_urls:
            if img['src'] not in html_content:
                logger.warning(f"[HTML_GEN] Görsel HTML'de kullanılmamış olabilir: {img['name']}")
                
        # Logo ve SVG arkaplanların kullanıldığını kontrol et
        if logo_uri and logo_uri not in html_content:
            logger.warning(f"[HTML_GEN] Logo HTML'de kullanılmamış olabilir")
        
        if cover_bg_uri and cover_bg_uri not in html_content:
            logger.warning(f"[HTML_GEN] Kapak arkaplanı HTML'de kullanılmamış olabilir")
            
        if general_bg_uri and general_bg_uri not in html_content:
            logger.warning(f"[HTML_GEN] Genel arkaplan HTML'de kullanılmamış olabilir")
            
        logger.info(f"[HTML_GEN] Dinamik HTML başarıyla oluşturuldu: {len(html_content)} karakter")
        return html_content
        
    except Exception as e:
        logger.error(f"[HTML_GEN] HTML oluşturulurken hata: {str(e)}")
        raise ValueError(f"Dinamik HTML oluşturulurken hata: {str(e)}")
