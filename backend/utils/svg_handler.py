# backend/utils/svg_handler.py

import base64
from pathlib import Path
from typing import Dict, List
import mimetypes

class SVGAssetHandler:
    """Handles SVG assets for projects with special naming conventions"""
    
    # Turkish to English mapping for common SVG types
    SVG_MAPPINGS = {
        'kapak_foto': 'section_divider',
        'cerceve': 'frame',
        'arkaplan': 'background',
        'logo': 'logo',
        'banner': 'banner'
    }
    
    def __init__(self, project_slug: str, base_dir: Path):
        self.project_slug = project_slug
        self.assets_dir = base_dir / "data" / "uploads" / "active_report" / project_slug / "svgs"
        self.project_assets_dir = base_dir / "static" / "project_assets" / project_slug
        
    def get_svg_assets(self) -> Dict[str, str]:
        """Get all SVG assets for the project"""
        svg_assets = {}
        
        # Check both directories
        for directory in [self.assets_dir, self.project_assets_dir]:
            if directory.exists():
                for svg_file in directory.glob("*.svg"):
                    # Normalize filename
                    normalized_name = self._normalize_svg_name(svg_file.stem)
                    svg_assets[normalized_name] = str(svg_file)
                    
        return svg_assets
    
    def _normalize_svg_name(self, filename: str) -> str:
        """Normalize Turkish SVG names to standard keys"""
        filename_lower = filename.lower()
        
        # Check for known mappings
        for turkish, english in self.SVG_MAPPINGS.items():
            if turkish in filename_lower:
                return english
                
        # Return original if no mapping found
        return filename_lower
    
    def get_project_specific_rules(self) -> Dict[str, any]:
        """Get project-specific SVG placement rules"""
        if self.project_slug == "v_metroway":
            return {
                "use_section_dividers": True,
                "section_divider_svg": "kapak_foto",
                "background_frame_svg": "metroway_frame",
                "divider_sections": [
                    "AÇILIŞ ÖNCESİ SÜREÇLER VE İNŞAAT",
                    "KİRALAMA VE OPERASYONEL ÇALIŞMALAR", 
                    "PAZARLAMA"
                ]
            }
        return {
            "use_section_dividers": False
        }
    
    def convert_svgs_to_base64(self, html_content: str, svg_assets: Dict[str, str]) -> str:
        """Convert SVG references in HTML to base64"""
        for svg_name, svg_path in svg_assets.items():
            if Path(svg_path).exists():
                with open(svg_path, 'rb') as f:
                    svg_content = f.read()
                    base64_svg = base64.b64encode(svg_content).decode('utf-8')
                    
                # Replace all references to this SVG
                patterns = [
                    f'src="{svg_name}.svg"',
                    f'url("{svg_name}.svg")',
                    f'href="{svg_name}.svg"',
                    f'src="assets/{svg_name}.svg"',
                    f'url("assets/{svg_name}.svg")'
                ]
                
                replacement = f'data:image/svg+xml;base64,{base64_svg}'
                
                for pattern in patterns:
                    if 'src=' in pattern:
                        html_content = html_content.replace(pattern, f'src="{replacement}"')
                    elif 'url(' in pattern:
                        html_content = html_content.replace(pattern, f'url("{replacement}")')
                    elif 'href=' in pattern:
                        html_content = html_content.replace(pattern, f'href="{replacement}"')
                        
        return html_content