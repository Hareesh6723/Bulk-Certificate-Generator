import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job import GenerationJob, JobStatus
from app.models.certificate import CertificateRecipient, CertificateStatus
from app.schemas.job import JobCreateRequest
from app.services.certificate_generator import CertificateGenerator
from app.config import settings

logger = logging.getLogger(__name__)

class JobService:

    @staticmethod
    def create_job(db: Session, request: JobCreateRequest) -> GenerationJob:
        """Initializes a new job and pre-creates recipient certificate records."""
        issue_date_val = request.issue_date or datetime.now().strftime("%B %d, %Y")
        issuer_val = request.issuer_name or settings.DEFAULT_ISSUER
        sig_name_val = request.signatory_name or settings.DEFAULT_SIGNATORY_NAME
        sig_title_val = request.signatory_title or settings.DEFAULT_SIGNATORY_TITLE

        job = GenerationJob(
            event_title=request.event_title,
            issuer_name=issuer_val,
            signatory_name=sig_name_val,
            signatory_title=sig_title_val,
            issue_date=issue_date_val,
            template_theme=request.template_theme or "classic_gold",
            status=JobStatus.PENDING,
            total_recipients=len(request.recipients),
            processed_count=0,
            success_count=0,
            failure_count=0,
        )
        db.add(job)
        db.flush()  # Allocate job.id

        # Insert recipient records
        for r in request.recipients:
            cert = CertificateRecipient(
                job_id=job.id,
                recipient_name=r.name,
                recipient_email=r.email,
                metadata_json=json.dumps(r.metadata or {}),
                status=CertificateStatus.PENDING,
            )
            db.add(cert)

        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def process_job_sync_or_async(cls, job_id: str, db: Optional[Session] = None):
        """
        Background task worker to process certificates one by one with failure isolation.
        Can run in FastAPI BackgroundTasks or separate worker thread.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found for background processing")
                return

            job.status = JobStatus.PROCESSING
            job.processed_count = 0
            job.success_count = 0
            job.failure_count = 0
            db.commit()

            # Process each certificate record
            certificates = db.query(CertificateRecipient).filter(
                CertificateRecipient.job_id == job_id
            ).all()

            for cert in certificates:
                cert.status = CertificateStatus.GENERATING
                db.commit()

                try:
                    meta = json.loads(cert.metadata_json) if cert.metadata_json else {}
                    
                    pdf_path = CertificateGenerator.generate_pdf(
                        certificate_id=cert.id,
                        recipient_name=cert.recipient_name,
                        recipient_email=cert.recipient_email,
                        event_title=job.event_title,
                        issuer_name=job.issuer_name,
                        signatory_name=job.signatory_name,
                        signatory_title=job.signatory_title,
                        issue_date=job.issue_date,
                        template_theme=job.template_theme,
                        metadata=meta,
                    )
                    
                    cert.status = CertificateStatus.SUCCESS
                    cert.pdf_path = pdf_path
                    cert.generated_at = datetime.now(timezone.utc)
                    job.success_count += 1

                except Exception as ex:
                    logger.warning(f"Error generating certificate {cert.id} for {cert.recipient_name}: {ex}")
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = str(ex)
                    job.failure_count += 1

                finally:
                    job.processed_count += 1
                    db.commit()

            # Determine final job status
            if job.failure_count == 0 and job.success_count > 0:
                job.status = JobStatus.COMPLETED
            elif job.success_count > 0 and job.failure_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED
            else:
                job.status = JobStatus.FAILED

            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Job {job_id} finished with status: {job.status.value}")

        except Exception as e:
            logger.exception(f"Fatal error executing job {job_id}: {e}")
            if job:
                job.status = JobStatus.FAILED
                db.commit()
        finally:
            if should_close:
                db.close()
