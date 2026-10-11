import os
import re
import zipfile
from pathlib import Path
from typing import List
from app.config import settings
from app.models.certificate import CertificateRecipient, CertificateStatus

def sanitize_filename(name: str) -> str:
    """Sanitize strings for safe filenames across Windows and Linux."""
    return re.sub(r'[\\/*?:"<>| ]', '_', name).strip('_')

class ZipService:
    @staticmethod
    def create_job_zip(job_id: str, event_title: str, certificates: List[CertificateRecipient]) -> str:
        """
        Creates a zip file containing all successfully generated certificates for a job.
        Returns the path to the created zip file.
        """
        safe_title = sanitize_filename(event_title)[:40]
        zip_filename = f"{safe_title}_{job_id[:8]}_certificates.zip"
        zip_path = settings.TEMP_DIR / zip_filename

        # Filter only successful certificates with existing files
        valid_certs = [
            cert for cert in certificates 
            if cert.status == CertificateStatus.SUCCESS and cert.pdf_path and os.path.exists(cert.pdf_path)
        ]

        if not valid_certs:
            raise ValueError("No successful certificates available to zip")

        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zip_file:
            for cert in valid_certs:
                recipient_slug = sanitize_filename(cert.recipient_name)
                archive_name = f"{recipient_slug}_{cert.id[:6]}.pdf"
                zip_file.write(cert.pdf_path, arcname=archive_name)

        return str(zip_path)
