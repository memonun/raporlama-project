"""
Template işleme ve yükleme yardımcıları.
"""
import os
from pathlib import Path
from string import Template
from datetime import datetime

def get_current_year():
    """Mevcut yılı döndürür"""
    return datetime.now().year

def get_template_path(template_name, template_type='html'):
    """
    Belirtilen template dosyasının tam yolunu döndürür.
    
    Args:
        template_name: Template dosyasının adı (uzantısız)
        template_type: Template türü ('html' veya 'txt')
        
    Returns:
        Template dosyasının tam yolu
    """
    # Proje kök dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = Path(current_dir).parent
    
    # Template dosyasının yolu
    template_path = os.path.join(base_dir, "templates", "email", f"{template_name}.{template_type}")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"{template_type} template bulunamadı: {template_name}")
    
    return template_path

def render_template(template_name, template_type='html', **kwargs):
    """
    Belirtilen template'i verilen değişkenlerle işler ve sonucu döndürür.
    
    Args:
        template_name: Template dosyasının adı (uzantısız)
        template_type: Template türü ('html' veya 'txt')
        kwargs: Template'e aktarılacak değişkenler
        
    Returns:
        İşlenmiş template içeriği
    """
    template_path = get_template_path(template_name, template_type)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Template'i işle
    template = Template(template_content)
    
    # Tüm çift süslü parantezleri tek süslü paranteze dönüştür (Template sınıfı için)
    template_content_fixed = template_content.replace('{{', '${').replace('}}', '}')
    template = Template(template_content_fixed)
    
    # Yılı otomatik ekle
    if 'current_year' not in kwargs:
        kwargs['current_year'] = get_current_year()
    
    return template.safe_substitute(**kwargs) 