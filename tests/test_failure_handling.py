import pytest
from app.services.job_service import JobService

def test_individual_certificate_failure_isolation(client, db_session):
    """
    Validates that if generating one certificate raises an exception,
    the remaining valid certificates in the bulk request are successfully generated.
    The job status finishes as PARTIALLY_COMPLETED and identifies failed recipients.
    """
    payload = {
        "event_title": "Resilience & Fault Tolerance Workshop",
        "issuer_name": "Antigravity Testing Org",
        "recipients": [
            {
                "name": "Alice Green",
                "email": "alice.green@example.com",
                "metadata": {"grade": "A"}
            },
            {
                "name": "FAIL_TEST_RECIPIENT",
                "email": "will.fail@example.com",
                "metadata": {"grade": "N/A"}
            },
            {
                "name": "Bob White",
                "email": "bob.white@example.com",
                "metadata": {"grade": "A+"}
            }
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["job_id"]

    # Fetch resulting job status (background task runs during client.post in TestClient)
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()

    # Job level assertions
    assert data["status"] == "PARTIALLY_COMPLETED"
    assert data["total_recipients"] == 3
    assert data["processed_count"] == 3
    assert data["success_count"] == 2
    assert data["failure_count"] == 1

    # Individual certificates breakdown
    certs_by_name = {c["recipient_name"]: c for c in data["certificates"]}

    # Alice Green must succeed
    assert certs_by_name["Alice Green"]["status"] == "SUCCESS"
    assert certs_by_name["Alice Green"]["download_url"] is not None
    assert certs_by_name["Alice Green"]["error_message"] is None

    # FAIL_TEST_RECIPIENT must fail with captured error message
    assert certs_by_name["FAIL_TEST_RECIPIENT"]["status"] == "FAILED"
    assert certs_by_name["FAIL_TEST_RECIPIENT"]["download_url"] is None
    assert "Deliberate failure triggered for testing" in certs_by_name["FAIL_TEST_RECIPIENT"]["error_message"]

    # Bob White must succeed (proves failure did NOT prevent subsequent certificates)
    assert certs_by_name["Bob White"]["status"] == "SUCCESS"
    assert certs_by_name["Bob White"]["download_url"] is not None
    assert certs_by_name["Bob White"]["error_message"] is None
