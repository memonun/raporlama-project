from pydantic import BaseModel
from typing import Dict, List, Optional, Literal
from enum import Enum

class ComponentStatus(str, Enum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    IN_PROGRESS = "in_progress"

class Question(BaseModel):
    id: str
    text: str
    type: Literal["text", "checkbox", "select", "file", "textarea"]
    required: bool
    options: Optional[List[str]] = None

class Component(BaseModel):
    name: str
    status: ComponentStatus
    questions: List[Question]
    answers: Dict[str, str] = {}
    completion_percentage: int = 0
    responsible_email: Optional[str] = None

class ReportData(BaseModel):
    project_name: str
    created_at: str  # ISO format tarih
    last_updated: str  # ISO format tarih
    components: Dict[str, Component]
    generated_report: Optional[str] = None
    pdf_path: Optional[str] = None 