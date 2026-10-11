from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import CertificateRecipient, CertificateStatus
from app.models.job import GenerationJob
from app.schemas.certificate import VerificationResponse

router = APIRouter(tags=["Verification"])

def mask_email(email: str) -> str:
    """Mask email for privacy, e.g. j***n@example.com"""
    if not email or "@" not in email:
        return email
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"

@router.get("/api/v1/verify/{certificate_id}", response_model=VerificationResponse)
def verify_certificate_api(certificate_id: str, db: Session = Depends(get_db)):
    """
    Public API endpoint to verify credential authenticity.
    """
    cert = db.query(CertificateRecipient).filter(CertificateRecipient.id == certificate_id).first()
    if not cert:
        return VerificationResponse(
            is_valid=False,
            certificate_id=certificate_id,
            status="NOT_FOUND"
        )

    job = db.query(GenerationJob).filter(GenerationJob.id == cert.job_id).first()
    is_valid = (cert.status == CertificateStatus.SUCCESS)

    return VerificationResponse(
        is_valid=is_valid,
        certificate_id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email_masked=mask_email(cert.recipient_email),
        event_title=job.event_title if job else None,
        issuer_name=job.issuer_name if job else None,
        signatory_name=job.signatory_name if job else None,
        signatory_title=job.signatory_title if job else None,
        issue_date=job.issue_date if job else None,
        issued_at=cert.generated_at,
        status=cert.status.value if hasattr(cert.status, "value") else str(cert.status),
        download_url=f"/api/v1/certificates/{cert.id}/download" if is_valid else None
    )

@router.get("/verify/{certificate_id}", response_class=HTMLResponse)
def verify_certificate_html(certificate_id: str, db: Session = Depends(get_db)):
    """
    Public web verification page displayed when someone scans the certificate QR code.
    """
    cert = db.query(CertificateRecipient).filter(CertificateRecipient.id == certificate_id).first()
    if not cert or cert.status != CertificateStatus.SUCCESS:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Certificate Verification - Invalid</title>
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap">
                <style>
                    body {{ font-family: 'Outfit', sans-serif; background-color: #f8fafc; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 24px 24px; color: #0f172a; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 1.5rem; }}
                    .card {{ background: #ffffff; padding: 2.75rem 2.25rem; border-radius: 1rem; max-width: 480px; text-align: center; border: 1px solid #fecaca; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.06); }}
                    .badge {{ display: inline-block; background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; padding: 0.35rem 1rem; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; margin-bottom: 1.25rem; }}
                    h1 {{ margin: 0 0 0.75rem; font-size: 1.5rem; color: #0f172a; font-weight: 700; }}
                    p {{ color: #64748b; line-height: 1.6; margin-bottom: 1.75rem; font-size: 0.925rem; }}
                    code {{ background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.85rem; color: #0f172a; }}
                    a {{ display: inline-block; background: #0f172a; color: white; text-decoration: none; padding: 0.7rem 1.5rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.875rem; }}
                    a:hover {{ background: #1e293b; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="badge">✕ UNVERIFIED CREDENTIAL</div>
                    <h1>Certificate Not Found</h1>
                    <p>The credential ID <code>{certificate_id}</code> could not be verified in the registry or generation was incomplete.</p>
                    <a href="/">Return to Dashboard</a>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )

    job = db.query(GenerationJob).filter(GenerationJob.id == cert.job_id).first()
    event_title = job.event_title if job else "Course Certification"
    issuer = job.issuer_name if job else "Global Academy of Technology"
    issue_date = job.issue_date if job else "N/A"
    recipient = cert.recipient_name
    masked_email = mask_email(cert.recipient_email)

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verified Credential - {recipient}</title>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap">
            <style>
                * {{ box-sizing: border-box; }}
                body {{
                    font-family: 'Outfit', sans-serif;
                    background-color: #f8fafc;
                    background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
                    background-size: 24px 24px;
                    color: #0f172a;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 1.5rem;
                }}
                .card {{
                    background: #ffffff;
                    padding: 3rem 2.5rem;
                    border-radius: 1rem;
                    max-width: 520px;
                    width: 100%;
                    text-align: center;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
                }}
                .badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.4rem;
                    background: #ecfdf5;
                    color: #065f46;
                    border: 1px solid #a7f3d0;
                    padding: 0.35rem 1.1rem;
                    border-radius: 9999px;
                    font-size: 0.8rem;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    margin-bottom: 1.5rem;
                }}
                .recipient {{
                    font-size: 1.85rem;
                    font-weight: 700;
                    color: #0f172a;
                    margin: 0 0 0.35rem;
                }}
                .email {{
                    color: #64748b;
                    font-size: 0.9rem;
                    margin-bottom: 1.75rem;
                }}
                .details-box {{
                    background: #f8fafc;
                    border-radius: 0.75rem;
                    padding: 1.25rem 1.5rem;
                    margin-bottom: 1.75rem;
                    text-align: left;
                    border: 1px solid #e2e8f0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 0.55rem 0;
                    border-bottom: 1px solid #edf2f7;
                    font-size: 0.875rem;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    color: #64748b;
                }}
                .detail-val {{
                    font-weight: 600;
                    color: #0f172a;
                    text-align: right;
                }}
                .btn-group {{
                    display: flex;
                    gap: 0.75rem;
                    justify-content: center;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0.75rem 1.4rem;
                    border-radius: 0.5rem;
                    font-weight: 600;
                    font-size: 0.875rem;
                    text-decoration: none;
                    transition: all 0.15s ease;
                }}
                .btn-primary {{
                    background: #0f172a;
                    color: #ffffff;
                }}
                .btn-primary:hover {{
                    background: #1e293b;
                }}
                .btn-secondary {{
                    background: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                }}
                .btn-secondary:hover {{
                    background: #f1f5f9;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="badge">
                    <span>✓</span> OFFICIAL CREDENTIAL VERIFIED
                </div>
                <div class="recipient">{recipient}</div>
                <div class="email">{masked_email}</div>
                
                <div class="details-box">
                    <div class="detail-row">
                        <span class="detail-label">Certification Program</span>
                        <span class="detail-val">{event_title}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Issuing Authority</span>
                        <span class="detail-val">{issuer}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date of Issuance</span>
                        <span class="detail-val">{issue_date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Credential ID</span>
                        <span class="detail-val" style="font-family: monospace; font-size: 0.8rem; background: #e2e8f0; padding: 0.15rem 0.4rem; border-radius: 4px;">{certificate_id}</span>
                    </div>
                </div>

                <div class="btn-group">
                    <a href="/api/v1/certificates/{certificate_id}/download" class="btn btn-primary" download>Download Official PDF</a>
                    <a href="/" class="btn btn-secondary">Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """
    )
