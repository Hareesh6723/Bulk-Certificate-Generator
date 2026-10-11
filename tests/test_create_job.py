import pytest
from app.models.job import GenerationJob, JobStatus
from app.models.certificate import CertificateRecipient

def test_create_bulk_generation_job_success(client, db_session):
    payload = {
        "event_title": "Advanced Python Architecture Workshop",
        "issuer_name": "Antigravity Engineering",
        "signatory_name": "Dr. Alan Turing",
        "signatory_title": "Chief Scientist",
        "issue_date": "2026-10-11",
        "template_theme": "classic_gold",
        "recipients": [
            {
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "metadata": {"grade": "Distinction", "hours": "30"}
            },
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "metadata": {"grade": "Excellence", "hours": "30"}
            }
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "job_id" in data
    assert data["total_recipients"] == 2
    assert data["status"] == "PENDING"
    assert "/api/v1/jobs/" in data["status_url"]

    # Verify database state
    job_id = data["job_id"]
    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job is not None
    assert job.event_title == "Advanced Python Architecture Workshop"
    assert job.total_recipients == 2

    recipients = db_session.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()
    assert len(recipients) == 2
    names = {r.recipient_name for r in recipients}
    assert "Grace Hopper" in names
    assert "Ada Lovelace" in names
