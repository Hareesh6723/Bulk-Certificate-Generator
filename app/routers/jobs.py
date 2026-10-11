import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import GenerationJob, JobStatus
from app.models.certificate import CertificateRecipient, CertificateStatus
from app.schemas.job import JobCreateRequest, JobCreateResponse, JobStatusResponse
from app.schemas.certificate import CertificateResponse
from app.services.job_service import JobService
from app.services.zip_service import ZipService
from app.config import settings

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def serialize_certificate(cert: CertificateRecipient) -> CertificateResponse:
    metadata_dict = {}
    if cert.metadata_json:
        try:
            metadata_dict = json.loads(cert.metadata_json)
        except Exception:
            metadata_dict = {}

    return CertificateResponse(
        id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status.value if hasattr(cert.status, "value") else str(cert.status),
        metadata=metadata_dict,
        download_url=f"/api/v1/certificates/{cert.id}/download" if cert.status == CertificateStatus.SUCCESS else None,
        preview_url=f"/api/v1/certificates/{cert.id}/preview" if cert.status == CertificateStatus.SUCCESS else None,
        verification_url=f"/verify/{cert.id}",
        error_message=cert.error_message,
        created_at=cert.created_at,
        generated_at=cert.generated_at,
    )

@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_bulk_generation_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits a bulk certificate generation request.
    Validates recipient list, creates job record, and dispatches background processing.
    """
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Recipient list cannot be empty."
        )

    # Create job in database
    job = JobService.create_job(db, request)

    # Dispatch asynchronous background task
    background_tasks.add_task(JobService.process_job_sync_or_async, job.id)

    return JobCreateResponse(
        job_id=job.id,
        event_title=job.event_title,
        status=job.status,
        total_recipients=job.total_recipients,
        message="Bulk certificate generation job accepted and processing in background.",
        status_url=f"/api/v1/jobs/{job.id}"
    )

@router.get("", response_model=List[JobStatusResponse])
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists recent certificate generation jobs."""
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    
    response = []
    for job in jobs:
        progress = round((job.processed_count / job.total_recipients * 100), 1) if job.total_recipients > 0 else 0.0
        response.append(JobStatusResponse(
            job_id=job.id,
            event_title=job.event_title,
            issuer_name=job.issuer_name,
            signatory_name=job.signatory_name,
            signatory_title=job.signatory_title,
            issue_date=job.issue_date,
            template_theme=job.template_theme,
            status=job.status,
            total_recipients=job.total_recipients,
            processed_count=job.processed_count,
            success_count=job.success_count,
            failure_count=job.failure_count,
            progress_percentage=progress,
            zip_download_url=f"/api/v1/jobs/{job.id}/download-zip" if job.success_count > 0 else None,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            certificates=[]  # Omit recipients in list view for performance
        ))
    return response

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the current progress, status, and list of recipient certificates for a specific job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Job with ID '{job_id}' not found."
        )

    progress = round((job.processed_count / job.total_recipients * 100), 1) if job.total_recipients > 0 else 0.0
    
    certs_data = [serialize_certificate(c) for c in job.certificates]

    return JobStatusResponse(
        job_id=job.id,
        event_title=job.event_title,
        issuer_name=job.issuer_name,
        signatory_name=job.signatory_name,
        signatory_title=job.signatory_title,
        issue_date=job.issue_date,
        template_theme=job.template_theme,
        status=job.status,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        progress_percentage=progress,
        zip_download_url=f"/api/v1/jobs/{job.id}/download-zip" if job.success_count > 0 else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        certificates=certs_data
    )

@router.get("/{job_id}/download-zip")
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Bundles all successfully generated certificates for a job into a ZIP archive and triggers download.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Job with ID '{job_id}' not found."
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No successful certificates generated yet for this job."
        )

    try:
        zip_filepath = ZipService.create_job_zip(job.id, job.event_title, job.certificates)
        return FileResponse(
            path=zip_filepath,
            filename=f"{job.event_title.replace(' ', '_')}_certificates.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
