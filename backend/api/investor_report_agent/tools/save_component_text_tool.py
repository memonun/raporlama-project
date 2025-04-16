from agency_swarm.tools import BaseTool
from pydantic import Field
from pathlib import Path
from typing import List, Tuple
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Base paths – adjust relative to this file's location
BASE_DIR = Path(__file__).parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
ACTIVE_REPORT_DIR = UPLOADS_DIR / "active_report"

def ensure_directory_structure(project_name: str) -> None:
    """
    Creates the necessary directory structure under ACTIVE_REPORT_DIR for a given project.
    """
    project_dir = ACTIVE_REPORT_DIR / project_name.lower()
    images_dir = project_dir / "images"
    text_dir = project_dir / "text"
    
    for dir_path in [project_dir, images_dir, text_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"[FILE] Dizin oluşturuldu: {dir_path}")

class SaveComponentTextTool(BaseTool):
    """
    Agentic tool to save a component's text content.
    This tool updates (or creates) a JSON file storing texts for all components.
    """
    project_name: str = Field(..., description="Project name")
    component_name: str = Field(..., description="Component name")
    text_content: str = Field(..., description="Text content to be saved for the component")
    
    def run(self) -> Tuple[bool, str]:
        """
        Returns:
            Tuple (success: bool, error_message: str)
        """
        try:
            ensure_directory_structure(self.project_name)
            components_file = ACTIVE_REPORT_DIR / self.project_name.lower() / "text" / "components.json"
            components_data = {}
            if components_file.exists():
                with open(components_file, "r", encoding="utf-8") as f:
                    components_data = json.load(f)
            components_data[self.component_name] = self.text_content
            with open(components_file, "w", encoding="utf-8") as f:
                json.dump(components_data, f, ensure_ascii=False, indent=2)
            logger.info(f"[SaveText] Bileşen metni kaydedildi: {self.component_name} - {self.project_name}")
            return True, ""
        except Exception as e:
            logger.error(f"[SaveText] Hata: {str(e)}", exc_info=True)
            return False, str(e)