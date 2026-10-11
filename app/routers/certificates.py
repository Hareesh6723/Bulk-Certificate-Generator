import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import CertificateRecipient, CertificateStatus
from app.services.zip_service import sanitize_filename

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Downloads an individual generated certificate as a PDF file attachment.
    """
    cert = db.query(CertificateRecipient).filter(CertificateRecipient.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Certificate '{certificate_id}' not found."
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.pdf_path or not os.path.exists(cert.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate file is not ready or generation failed. Current status: {cert.status}"
        )

    filename = f"{sanitize_filename(cert.recipient_name)}_Certificate.pdf"
    return FileResponse(
        path=cert.pdf_path,
        filename=filename,
        media_type="application/pdf"
    )

@router.get("/{certificate_id}/preview")
def preview_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Streams the certificate PDF inline for browser viewing / iframe preview.
    """
    cert = db.query(CertificateRecipient).filter(CertificateRecipient.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Certificate '{certificate_id}' not found."
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.pdf_path or not os.path.exists(cert.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate file is not available. Current status: {cert.status}"
        )

    return FileResponse(
        path=cert.pdf_path,
        media_type="application/pdf"
    )
