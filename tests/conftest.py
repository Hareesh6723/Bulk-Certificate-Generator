import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.config import settings

@pytest.fixture(scope="session")
def temp_test_dir():
    temp_dir = tempfile.mkdtemp(prefix="cert_tests_")
    orig_storage = settings.STORAGE_DIR
    orig_certs = settings.CERTIFICATES_DIR
    orig_qr = settings.QR_CODES_DIR
    orig_temp = settings.TEMP_DIR

    # Override config paths for testing
    p = Path(temp_dir)
    settings.STORAGE_DIR = p
    settings.CERTIFICATES_DIR = p / "certificates"
    settings.QR_CODES_DIR = p / "qrcodes"
    settings.TEMP_DIR = p / "temp"

    settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    settings.QR_CODES_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    yield p

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    settings.STORAGE_DIR = orig_storage
    settings.CERTIFICATES_DIR = orig_certs
    settings.QR_CODES_DIR = orig_qr
    settings.TEMP_DIR = orig_temp

@pytest.fixture(scope="function")
def db_session(temp_test_dir):
    test_db_path = temp_test_dir / "test.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    import app.database
    import app.services.job_service
    orig_session_local_db = app.database.SessionLocal
    orig_session_local_srv = app.services.job_service.SessionLocal
    app.database.SessionLocal = TestingSessionLocal
    app.services.job_service.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        app.database.SessionLocal = orig_session_local_db
        app.services.job_service.SessionLocal = orig_session_local_srv

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
