from typing import List, Optional
from pydantic import BaseModel

class ShareReportRequest(BaseModel):
    """Email ile rapor paylaşma isteği"""
    project_name: str
    report_date: str
    email_addresses: List[str]
    report_id: Optional[str] = None 