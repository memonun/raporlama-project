from agency_swarm.tools import BaseTool
from pydantic import Field
from pathlib import Path
from typing import List, Tuple
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

class EnsureDirectoryStructureTool(BaseTool):
    """
    Agentic tool to create the necessary active report directories for a project.
    """
    project_name: str = Field(..., description="Project name for which to create directory structure")
    
    def run(self) -> bool:
        try:
            ensure_directory_structure(self.project_name)
            return True
        except Exception as e:
            logger.error(f"[EnsureDirectory] Hata: {str(e)}", exc_info=True)
            return False