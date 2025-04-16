from agency_swarm.tools import BaseTool
from pydantic import Field
from pathlib import Path
from typing import List, Tuple
import shutil
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Base paths – adjust relative to this file's location
BASE_DIR = Path(__file__).parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
ACTIVE_REPORT_DIR = UPLOADS_DIR / "active_report"

class CleanActiveReportTool(BaseTool):
    """
    Agentic tool to clean (delete) the active report directory for a project.
    This is typically used after a report is finalized.
    """
    project_name: str = Field(..., description="Project name")
    
    def run(self) -> bool:
        try:
            project_dir = ACTIVE_REPORT_DIR / self.project_name.lower()
            if not project_dir.exists():
                logger.warning(f"[CleanReport] Temizlenecek dizin bulunamadı: {project_dir}")
                return True
            shutil.rmtree(project_dir)
            logger.info(f"[CleanReport] Aktif rapor dizini temizlendi: {project_dir}")
            return True
        except Exception as e:
            logger.error(f"[CleanReport] Hata: {str(e)}", exc_info=True)
            return False