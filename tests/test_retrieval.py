import io
import zipfile
import pytest
from app.services.job_service import JobService

def test_retrieve_individual_certificate_pdf(client, db_session):
    payload = {
        "event_title": "Cloud Computing Fundamentals",
        "recipients": [
            {"name": "Dorothy Vaughan", "email": "dorothy@example.com"}
        ]
    }

    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    JobService.process_job_sync_or_async(job_id)

    status_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = status_data["certificates"][0]["id"]

    # 1. Test Download endpoint (attachment)
    download_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert "attachment" in download_res.headers.get("content-disposition", "")
    assert download_res.content[:5] == b"%PDF-"

    # 2. Test Preview endpoint (inline)
    preview_res = client.get(f"/api/v1/certificates/{cert_id}/preview")
    assert preview_res.status_code == 200
    assert preview_res.headers["content-type"] == "application/pdf"
    assert preview_res.content[:5] == b"%PDF-"

def test_retrieve_bulk_zip_archive(client, db_session):
    payload = {
        "event_title": "Quantum Information Science",
        "recipients": [
            {"name": "Richard Feynman", "email": "feynman@example.com"},
            {"name": "Niels Bohr", "email": "bohr@example.com"}
        ]
    }

    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    JobService.process_job_sync_or_async(job_id)

    # Download ZIP
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Inspect zip contents
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        file_list = zf.namelist()
        assert len(file_list) == 2
        # Verify both filenames end with .pdf
        for filename in file_list:
            assert filename.endswith(".pdf")
            pdf_bytes = zf.read(filename)
            assert pdf_bytes[:5] == b"%PDF-"

def test_retrieve_nonexistent_certificate_returns_404(client):
    res = client.get("/api/v1/certificates/random-non-existent-id/download")
    assert res.status_code == 404
