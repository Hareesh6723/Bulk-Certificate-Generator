import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database configuration (defaults to SQLite, easily swapped with PostgreSQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/storage/certificates.db")
    
    # File storage paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = STORAGE_DIR / "certificates"
    QR_CODES_DIR: Path = STORAGE_DIR / "qrcodes"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    
    # Host & verification base URL
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Default Certificate Configuration
    DEFAULT_ISSUER: str = "Global Academy of Technology"
    DEFAULT_SIGNATORY_NAME: str = "Dr. Eleanor Vance"
    DEFAULT_SIGNATORY_TITLE: str = "Director of Certification"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
settings.QR_CODES_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
