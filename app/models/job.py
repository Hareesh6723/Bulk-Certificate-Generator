import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_title = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    signatory_name = Column(String(255), nullable=True)
    signatory_title = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=False)
    template_theme = Column(String(50), default="classic_gold")
    
    status = Column(SAEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    total_recipients = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    certificates = relationship("CertificateRecipient", back_populates="job", cascade="all, delete-orphan", order_by="CertificateRecipient.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "event_title": self.event_title,
            "issuer_name": self.issuer_name,
            "signatory_name": self.signatory_name,
            "signatory_title": self.signatory_title,
            "issue_date": self.issue_date,
            "template_theme": self.template_theme,
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "total_recipients": self.total_recipients,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
