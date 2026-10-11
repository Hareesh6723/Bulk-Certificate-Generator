import pytest
from app.services.job_service import JobService

def test_public_credential_verification(client, db_session):
    payload = {
        "event_title": "Machine Learning Specialization",
        "issuer_name": "Stanford Online",
        "recipients": [
            {"name": "Andrew Ng", "email": "andrew.ng@example.com"}
        ]
    }

    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]
    JobService.process_job_sync_or_async(job_id)

    status_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = status_data["certificates"][0]["id"]

    # 1. API Verification endpoint
    verify_api_res = client.get(f"/api/v1/verify/{cert_id}")
    assert verify_api_res.status_code == 200
    data = verify_api_res.json()

    assert data["is_valid"] is True
    assert data["certificate_id"] == cert_id
    assert data["recipient_name"] == "Andrew Ng"
    assert data["event_title"] == "Machine Learning Specialization"
    assert data["issuer_name"] == "Stanford Online"
    assert data["download_url"] is not None
    # Masked email
    assert "@" in data["recipient_email_masked"]

    # 2. HTML Verification page (for QR code scan)
    verify_html_res = client.get(f"/verify/{cert_id}")
    assert verify_html_res.status_code == 200
    assert "text/html" in verify_html_res.headers["content-type"]
    assert "OFFICIAL CREDENTIAL VERIFIED" in verify_html_res.text
    assert "Andrew Ng" in verify_html_res.text

def test_unverified_credential(client):
    # API
    api_res = client.get("/api/v1/verify/invalid-certificate-uuid")
    assert api_res.status_code == 200
    assert api_res.json()["is_valid"] is False

    # HTML
    html_res = client.get("/verify/invalid-certificate-uuid")
    assert html_res.status_code == 404
    assert "Certificate Not Found" in html_res.text
