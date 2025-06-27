 # Validate project exists
from fastapi import HTTPException

from api.data_storage import get_project_data


def get_report_id_for_project(project_name: str) -> str:
        project_data = get_project_data(project_name)
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Check for active report
        active_report = project_data.get("active_report")
        if not active_report:
            raise HTTPException(status_code=400, detail="No active report found for this project")
        
        # Get report ID
        report_id = active_report.get("report_id")
        if not report_id:
            raise HTTPException(status_code=400, detail="Active report missing report_id")
        return report_id, project_data
