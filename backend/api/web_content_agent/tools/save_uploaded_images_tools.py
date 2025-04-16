from agency_swarm.tools import BaseTool
from pydantic import Field
from pathlib import Path
from typing import List, Tuple
import os
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

class SaveUploadedImageTool(BaseTool):
    """
    Agentic tool to save an uploaded image for a component.
    
    Instead of using UploadFile directly, this tool expects:
    - image_bytes: the raw file contents of the image.
    - original_filename: the name of the file as uploaded.
    """
    project_name: str = Field(..., description="Project name")
    component_name: str = Field(..., description="Component name")
    image_bytes: bytes = Field(..., description="Raw bytes of the image file")
    original_filename: str = Field(..., description="Original file name of the image")
    image_index: int = Field(0, description="Index number for the image")
    
    def run(self) -> Tuple[bool, str, str]:
        """
        Returns:
            Tuple (success: bool, new_filename: str, error_message: str)
        """
        try:
            ensure_directory_structure(self.project_name)
            comp_clean = self.component_name.lower()\
                          .replace(" ", "_")\
                          .replace("ı", "i")\
                          .replace("ğ", "g")\
                          .replace("ü", "u")\
                          .replace("ş", "s")\
                          .replace("ç", "c")\
                          .replace("ö", "o")
            _, file_ext = os.path.splitext(self.original_filename)
            file_ext = file_ext.lower()
            new_filename = f"{comp_clean}-{self.image_index}{file_ext}"
            image_dir = ACTIVE_REPORT_DIR / self.project_name.lower() / "images"
            file_path = image_dir / new_filename
            with open(file_path, "wb") as f:
                f.write(self.image_bytes)
            logger.info(f"[SaveImage] Görsel kaydedildi: {file_path}")
            return True, new_filename, ""
        except Exception as e:
            logger.error(f"[SaveImage] Hata: {str(e)}", exc_info=True)
            return False, "", str(e)           