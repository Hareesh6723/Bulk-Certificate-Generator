import os
import uuid
import pytest
from app.services.certificate_generator import CertificateGenerator

def test_generate_pdf_creates_valid_file(temp_test_dir):
    cert_id = str(uuid.uuid4())
    pdf_path = CertificateGenerator.generate_pdf(
        certificate_id=cert_id,
        recipient_name="Katherine Johnson",
        recipient_email="kjohnson@example.com",
        event_title="Orbital Mechanics and Advanced Mathematics",
        issuer_name="National Aeronautics Space Institute",
        signatory_name="Dr. Robert Gilruth",
        signatory_title="Director",
        issue_date="October 11, 2026",
        template_theme="classic_gold",
        metadata={"Grade": "Highest Distinction", "Hours": "120"}
    )

    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000

    # Verify standard PDF header magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

def test_generate_pdf_different_themes(temp_test_dir):
    themes = ["classic_gold", "sapphire_modern", "emerald_academic"]
    for theme in themes:
        cert_id = str(uuid.uuid4())
        pdf_path = CertificateGenerator.generate_pdf(
            certificate_id=cert_id,
            recipient_name="Test Student",
            recipient_email="student@example.com",
            event_title="Theme Test Course",
            issuer_name="Academy",
            template_theme=theme
        )
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000
