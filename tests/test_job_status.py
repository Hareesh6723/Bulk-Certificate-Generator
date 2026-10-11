import pytest
from app.services.job_service import JobService

def test_job_status_not_found(client):
    response = client.get("/api/v1/jobs/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_job_status_lifecycle_and_progress(client, db_session):
    from app.schemas.job import JobCreateRequest
    from app.schemas.certificate import RecipientInput

    # 1. Create job directly to verify initial PENDING state
    req = JobCreateRequest(
        event_title="Distributed Systems Engineering",
        issuer_name="MIT OpenCourse",
        recipients=[
            RecipientInput(name="Barbara Liskov", email="barbara@example.com"),
            RecipientInput(name="Leslie Lamport", email="leslie@example.com")
        ]
    )
    job = JobService.create_job(db_session, req)
    job_id = job.id

    # Check status endpoint while job is PENDING
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    initial_data = status_res.json()
    assert initial_data["total_recipients"] == 2
    assert initial_data["processed_count"] == 0
    assert initial_data["status"] == "PENDING"
    assert initial_data["progress_percentage"] == 0.0

    # 2. Run background processing
    JobService.process_job_sync_or_async(job_id, db=db_session)

    # Re-check status after completion
    status_res_after = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res_after.status_code == 200
    final_data = status_res_after.json()

    assert final_data["status"] == "COMPLETED"
    assert final_data["total_recipients"] == 2
    assert final_data["processed_count"] == 2
    assert final_data["success_count"] == 2
    assert final_data["failure_count"] == 0
    assert final_data["progress_percentage"] == 100.0
    assert final_data["completed_at"] is not None
    assert final_data["zip_download_url"] is not None
    assert len(final_data["certificates"]) == 2

    for cert in final_data["certificates"]:
        assert cert["status"] == "SUCCESS"
        assert cert["download_url"] is not None
        assert cert["preview_url"] is not None
        assert cert["verification_url"] is not None
        assert cert["error_message"] is None
