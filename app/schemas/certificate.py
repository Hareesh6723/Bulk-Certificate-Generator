import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Full name of the recipient")
    email: str = Field(..., description="Valid email address of the recipient")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional certificate details like grade, score, hours")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Recipient name must have at least 2 characters")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError(f"Invalid email format: '{v}'")
        return clean

class CertificateResponse(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    verification_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None

class VerificationResponse(BaseModel):
    is_valid: bool
    certificate_id: str
    recipient_name: Optional[str] = None
    recipient_email_masked: Optional[str] = None
    event_title: Optional[str] = None
    issuer_name: Optional[str] = None
    signatory_name: Optional[str] = None
    signatory_title: Optional[str] = None
    issue_date: Optional[str] = None
    issued_at: Optional[datetime] = None
    status: Optional[str] = None
    download_url: Optional[str] = None
