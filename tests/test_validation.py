import pytest

def test_validation_empty_recipients_list(client):
    payload = {
        "event_title": "Web Development Bootcamp",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_validation_missing_event_title(client):
    payload = {
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_validation_invalid_email_format(client):
    payload = {
        "event_title": "Data Science Masterclass",
        "recipients": [
            {"name": "Valid User", "email": "valid@example.com"},
            {"name": "Invalid User", "email": "not-an-email-at-all"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    err_detail = str(response.json()["detail"])
    assert "Invalid email format" in err_detail

def test_validation_name_too_short(client):
    payload = {
        "event_title": "Cloud Computing",
        "recipients": [
            {"name": "A", "email": "a@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
