from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any
from pathlib import Path
import logging
from config import PROJECT_PALETTES, CORPORATE_COLORS

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GetProjectStyleConfigTool(BaseTool):
    """
    Bir proje için stil yapılandırmasını alır: renk paleti, font bilgileri vb.
    WebContent Agent tarafından HTML oluştururken kullanılır.
    """
    
    project_name: str = Field(..., description="Stil yapılandırması alınacak proje adı")
    
    def run(self) -> Dict[str, Any]:
        """
        Verilen proje için renk paleti, font ve diğer stil bilgilerini içeren yapılandırmayı döndürür.
        """
        project_name = self.project_name.lower()
        
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
        font_dir = Path(__file__).parent.parent.parent.parent / 'static' / 'assets' / 'fonts'
        project_font_path = font_dir / "gothamrnd_light.ttf"
        project_font = None
        
        # Projeye özel bir font varsa
        if project_font_path.exists():
            logger.info(f"[HTML_GEN] Proje için özel font bulundu: {project_font_path.name}")
            project_font = project_font_path.name
        else:
            # Varsayılan font - Montserrat
            default_font_path = font_dir / "Montserrat-VariableFont_wght.ttf"
            if default_font_path.exists():
                logger.info(f"[HTML_GEN] Varsayılan font kullanılıyor: {default_font_path.name}")
                project_font = default_font_path.name
            else:
                # Herhangi bir font varsa
                available_fonts = list(font_dir.glob('*.ttf'))
                if available_fonts:
                    logger.info(f"[HTML_GEN] Kullanılabilir ilk font seçildi: {available_fonts[0].name}")
                    project_font = available_fonts[0].name
                else:
                    logger.warning(f"[HTML_GEN] Hiçbir font bulunamadı, sistem fontu kullanılacak.")
        
        # Şirket renkleri
        corporate_colors = CORPORATE_COLORS.copy()
        
        # Sonuç stil yapılandırması
        style_config = {
            'colors': project_colors,
            'corporate_colors': corporate_colors,
            'font': project_font,
            'layout': 'standard',  # veya 'modern', 'classic' gibi farklı düzenler eklenebilir
        }
        
        logger.info(f"[HTML_GEN] Proje stil yapılandırması başarıyla oluşturuldu: {self.project_name}")
        return style_config