from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from app.models.job import JobStatus
from app.schemas.certificate import RecipientInput, CertificateResponse

class JobCreateRequest(BaseModel):
    event_title: str = Field(..., min_length=2, max_length=255, description="Name of the course, event, or workshop")
    issuer_name: Optional[str] = Field(None, max_length=255, description="Issuing organization name")
    signatory_name: Optional[str] = Field(None, max_length=255, description="Signatory authority name")
    signatory_title: Optional[str] = Field(None, max_length=255, description="Signatory authority title")
    issue_date: Optional[str] = Field(None, description="Date of issue (e.g. YYYY-MM-DD or readable string)")
    template_theme: Optional[str] = Field("classic_gold", description="Template style: classic_gold, sapphire_modern, emerald_academic")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipients to generate certificates for")

    class Config:
        json_schema_extra = {
            "example": {
                "event_title": "Full-Stack AI Engineering Masterclass",
                "issuer_name": "Global Academy of Technology",
                "signatory_name": "Dr. Eleanor Vance",
                "signatory_title": "Director of Certification",
                "issue_date": "2026-10-11",
                "template_theme": "classic_gold",
                "recipients": [
                    {
                        "name": "Alice Johnson",
                        "email": "alice@example.com",
                        "metadata": {"grade": "Distinction", "hours": "40"}
                    },
                    {
                        "name": "Bob Smith",
                        "email": "bob@example.com",
                        "metadata": {"grade": "Merit", "hours": "40"}
                    }
                ]
            }
        }

class JobCreateResponse(BaseModel):
    job_id: str
    event_title: str
    status: JobStatus
    total_recipients: int
    message: str
    status_url: str

class JobStatusResponse(BaseModel):
    job_id: str
    event_title: str
    issuer_name: str
    signatory_name: Optional[str]
    signatory_title: Optional[str]
    issue_date: str
    template_theme: str
    status: JobStatus
    total_recipients: int
    processed_count: int
    success_count: int
    failure_count: int
    progress_percentage: float
    zip_download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    certificates: List[CertificateResponse] = []
