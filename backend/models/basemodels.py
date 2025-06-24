from typing import Any, Dict, List
from pydantic import BaseModel, Field

# Modeller
class ProjectRequest(BaseModel):
    project_name: str

class ReportRequest(BaseModel):
    project_name: str

class ComponentDataRequest(BaseModel):
    project_name: str
    component_name: str
    answers: Dict[str, str]

class GenerateReportRequest(BaseModel):
    project_name: str
    components_data: Dict[str, Dict[str, Any]] = {}
    

class EmailRequest(BaseModel):
    component_name: str
    project_name: str

class MissingInfoRequest(BaseModel):
    project_name: str
    component_name: str
    recipient_name: str

class MyHTMLResponse(BaseModel):
    content: str


class ProjectActionRequest(BaseModel):
    project_name: str

class ShareReportRequest(BaseModel):
    project_name: str
    email_addresses: List[str]

class DeleteFinalizedReportRequest(BaseModel):
  project_name: str


class DeleteProjectRequest(BaseModel):
    project_name: str

class ArchiveProjectRequest(BaseModel):
    project_name: str