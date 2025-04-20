from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any, ClassVar
import logging

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GetProjectStyleConfigTool(BaseTool):
    """
    Bir proje için stil yapılandırmasını alır: renk paleti ve kurumsal renkler.
    WebContent Agent tarafından HTML oluştururken kullanılır.
    Proje adına göre önceden tanımlanmış renk paletlerinden uygun olanı seçer.
    """
    
    project_name: str = Field(..., description="Stil yapılandırması alınacak proje adı")
    
    class ToolConfig:
        one_call_at_a_time = True

    # Kurumsal renkler tanımı - ClassVar olarak tanımlanıyor
    CORPORATE_COLORS: ClassVar[Dict[str, str]] = {
        "dark_blue": "#1a5276",
        "light_blue": "#2980b9",
        "navy": "#154360",
        "light_gray_bg": "#ebf5fb",
        "gray_alt": "#d6dbdf"
    }

    # Proje renk paletleri - ClassVar olarak tanımlanıyor
    PROJECT_PALETTES: ClassVar[Dict[str, Dict[str, str]]] = {
        'v_mall': {
            'primary': '#4b4b4b',
            'secondary': '#7c0a02',
            'background': '#e9ecef',
            'corporate_accent': '#1a5276',  # dark_blue
        },
        'v_metroway': {
            'primary': '#f7941d',
            'secondary': '#c1272d',
            'background': '#cccccc',
            'corporate_accent': '#2980b9',  # light_blue
        },
        'v_orman': {
            'primary': '#2e5339',
            'secondary': '#8b5e3c',
            'accent': '#a3d5d3',
            'corporate_accent': '#154360',  # navy
        }
    }
    
    def run(self) -> Dict[str, Any]:
        """
        Verilen proje için renk paleti ve kurumsal renkleri içeren yapılandırmayı döndürür.
        """
        project_name = self.project_name.lower()
        
        # Proje için renk paleti
        project_colors = self.PROJECT_PALETTES.get(project_name, {})
        if not project_colors:
            logger.warning(f"[HTML_GEN] Proje için ({project_name}) renk paleti bulunamadı. Varsayılan renkler kullanılacak.")
            # Varsayılan renk paleti
            project_colors = {
                'primary': '#3366CC',
                'secondary': '#6699FF',
                'accent': '#FF9900',
                'background': '#F5F7FA',
                'text': '#333333',
                'corporate_accent': self.CORPORATE_COLORS['dark_blue']
            }
        
        # Sonuç stil yapılandırması
        style_config = {
            'colors': project_colors,
            'corporate_colors': self.CORPORATE_COLORS,
            'layout': 'standard'  # veya 'modern', 'classic' gibi farklı düzenler eklenebilir
        }
        
        logger.info(f"[HTML_GEN] Proje stil yapılandırması başarıyla oluşturuldu: {self.project_name}")
        return style_config