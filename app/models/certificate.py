import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class CertificateRecipient(Base):
    __tablename__ = "certificate_recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    metadata_json = Column(Text, nullable=True)  # Store JSON string of additional attributes (grade, hours, etc.)
    
    status = Column(SAEnum(CertificateStatus), default=CertificateStatus.PENDING, nullable=False, index=True)
    pdf_path = Column(String(500), nullable=True)
    qr_code_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_at = Column(DateTime, nullable=True)

    job = relationship("GenerationJob", back_populates="certificates")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "recipient_name": self.recipient_name,
            "recipient_email": self.recipient_email,
            "metadata": self.metadata_json,
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "pdf_path": self.pdf_path,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
