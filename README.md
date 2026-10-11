# CertForge • Bulk Certificate Generator Engine & Studio

An enterprise-ready, high-performance backend API and interactive dashboard for bulk certificate generation. Built with **FastAPI**, **SQLAlchemy**, **ReportLab**, and **Pydantic v2**.

---

## 🌟 Key Highlights & Features

- **High-Throughput Bulk Processing:** Accepts batches of hundreds or thousands of recipients in a single request and returns an immediate asynchronous tracking job (`202 Accepted`).
- **Individual Error Isolation:** A failure during the generation of one certificate (e.g. malformed data or rendering exception) **never** fails the entire job. Other valid recipients continue and succeed smoothly.
- **Granular Lifecycle & Status Tracking:** Real-time job status (`PENDING` → `PROCESSING` → `COMPLETED` / `PARTIALLY_COMPLETED` / `FAILED`) with exact counters for total, processed, succeeded, and failed certificates.
- **Vector-Quality PDF Rendering:** Predefined certificate designs rendered at 300+ DPI vector quality using ReportLab with multi-tier ornamental borders, dynamic typography, authentic seal stamps, and signatures.
- **Dynamic QR Code Verification:** Every generated certificate embeds a verifiable QR code linking directly to a public verification endpoint (`/verify/{certificate_id}`).
- **Flexible Retrieval Options:**
  - Individual PDF direct download (`Content-Disposition: attachment`).
  - Inline browser PDF preview modal (`Content-Disposition: inline`).
  - **1-Click Bulk ZIP Archive:** Bundles all successful certificates for any job in a single `.zip` file.
- **Interactive UI Studio:** A clean, modern dark-themed web dashboard for uploading CSV files, manual table editing, real-time polling monitor, and live PDF preview.
- **Interactive API Documentation:** Native Swagger UI (`/docs`) and ReDoc (`/redoc`).

---

## 🏗️ Architecture & Design Decisions

### 1. Web Framework: FastAPI
- **Choice:** FastAPI over Flask/Django.
- **Rationale:** 
  - Native asynchronous non-blocking request handling.
  - Automatic request validation and serialization powered by Pydantic v2.
  - Built-in background execution (`BackgroundTasks`) allowing immediate HTTP response return without blocking the client.
  - Automatic, interactive OpenAPI/Swagger specification generation out-of-the-box.

### 2. Database & Data Model: SQLAlchemy 2.0
- **Choice:** Relational database with SQLAlchemy ORM.
- **Default Database:** SQLite (`storage/certificates.db`) for zero-configuration, instant local execution and test suite portability.
- **PostgreSQL Compatibility:** 100% compatible with PostgreSQL by simply supplying the standard `DATABASE_URL` environment variable (e.g. `postgresql://user:pass@localhost:5432/certdb`).
- **Schema Design:**
  - `GenerationJob`: Holds event metadata, issuing authority, template theme, overall job status, and aggregated counters (`total`, `processed`, `success`, `failure`).
  - `CertificateRecipient`: Tracks per-recipient progress, unique Credential UUID, generated PDF file path, QR code file path, and exact error message if an individual failure occurred.

### 3. Certificate Generation Engine: ReportLab
- **Choice:** ReportLab over headless Chrome / wkhtmltopdf / HTML-to-PDF wrappers.
- **Rationale:**
  - Pure Python vector graphics generation with zero external binary dependencies (no need to install Chromium, Puppeteer, or wkhtmltopdf binaries).
  - High performance: Generates printable, vector-crisp PDF certificates in tens of milliseconds per file.
  - Native drawing of ornamental borders, geometric corner brackets, official seals, and embedded QR codes.

### 4. Failure Handling Strategy
```
Client Request (N Recipients)
        │
        ▼
   [Validation] ─── Invalid Payload? ──► HTTP 422 Rejection
        │
        ▼ (Valid Job)
   [Job Created in DB] (Status: PENDING)
        │
        ▼ (FastAPI Background Task Dispatched)
   [Worker Iterates Over Recipients]
   ┌──────────────────────────────────────────────┐
   │ Recipient 1 ──► [Generate PDF] ──► SUCCESS   │
   │ Recipient 2 ──► [Generate PDF] ──► FAILED    │  ◄── Error caught & recorded;
   │ Recipient 3 ──► [Generate PDF] ──► SUCCESS   │      job continues uninterrupted!
   └──────────────────────────────────────────────┘
        │
        ▼
   [Final Job Status]
   • 100% Success       ──► COMPLETED
   • Mixed Success/Fail ──► PARTIALLY_COMPLETED
   • 0% Success         ──► FAILED
```

---

## 📂 Project Directory Structure

```
bulk-cert-generator/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application factory, middleware & routing
│   ├── config.py                   # Pydantic BaseSettings & directory setup
│   ├── database.py                 # SQLAlchemy engine, session maker & dependency
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py                  # GenerationJob model & JobStatus enum
│   │   └── certificate.py          # CertificateRecipient model & CertificateStatus enum
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py                  # JobCreateRequest, JobCreateResponse, JobStatusResponse
│   │   └── certificate.py          # RecipientInput, CertificateResponse, VerificationResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_generator.py# ReportLab PDF renderer with QR codes & themes
│   │   ├── job_service.py          # Job orchestration & error-isolated worker
│   │   └── zip_service.py          # ZIP bundling service for batch downloads
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── jobs.py                 # /api/v1/jobs endpoints
│   │   ├── certificates.py         # /api/v1/certificates download & preview endpoints
│   │   └── verification.py         # /api/v1/verify & /verify/{id} verification endpoints
│   └── static/
│       ├── index.html              # Modern web dashboard
│       ├── css/style.css           # Glassmorphism dark-theme styles
│       └── js/app.js               # Frontend controller, live polling & CSV handler
├── tests/
│   ├── conftest.py                 # Test DB fixtures & isolated storage setup
│   ├── test_create_job.py          # Job creation & persistence tests
│   ├── test_validation.py          # Recipient schema, email regex & field tests
│   ├── test_generation.py          # ReportLab PDF engine unit tests
│   ├── test_job_status.py          # Polling lifecycle & progress counter tests
│   ├── test_failure_handling.py    # Individual certificate failure isolation tests
│   ├── test_retrieval.py           # Single PDF download, inline preview & ZIP tests
│   └── test_verification.py        # Public verification API & HTML badge tests
├── sample_data/
│   └── recipients_sample.csv       # Sample CSV for quick manual/UI testing
├── storage/                        # Generated PDFs, QR codes & temp ZIPs
├── requirements.txt                # Production & development dependencies
├── pytest.ini                      # Pytest configuration
└── README.md                       # Complete documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python **3.10+** (Tested on Python 3.13)
- `pip` package manager

### 2. Installation & Virtual Environment Setup

```bash
# Navigate to the project directory
cd bulk-cert-generator

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started:
- **Interactive Web Studio:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running the Test Suite

The test suite covers:
1. Creating a generation job
2. Input validation (email regex, required fields, minimum name lengths)
3. Certificate generation (ReportLab vector PDF output, magic bytes `%PDF-`, themes)
4. Job status & progress polling (0% → 100%, counters)
5. Individual certificate failure isolation (verifying valid certificates succeed when one recipient throws an error)
6. Certificate retrieval (single PDF download, inline preview, and bulk ZIP bundle verification)
7. Verification portal (valid vs unverified credentials, masked recipient email)

Run the full test suite with verbose output:
```bash
pytest -v
```

Expected output:
```text
tests/test_create_job.py::test_create_bulk_generation_job_success PASSED
tests/test_failure_handling.py::test_individual_certificate_failure_isolation PASSED
tests/test_generation.py::test_generate_pdf_creates_valid_file PASSED
tests/test_generation.py::test_generate_pdf_different_themes PASSED
tests/test_job_status.py::test_job_status_not_found PASSED
tests/test_job_status.py::test_job_status_lifecycle_and_progress PASSED
tests/test_retrieval.py::test_retrieve_individual_certificate_pdf PASSED
tests/test_retrieval.py::test_retrieve_bulk_zip_archive PASSED
tests/test_retrieval.py::test_retrieve_nonexistent_certificate_returns_404 PASSED
tests/test_validation.py::test_validation_empty_recipients_list PASSED
tests/test_validation.py::test_validation_missing_event_title PASSED
tests/test_validation.py::test_validation_invalid_email_format PASSED
tests/test_validation.py::test_validation_name_too_short PASSED
tests/test_verification.py::test_public_credential_verification PASSED
tests/test_verification.py::test_unverified_credential PASSED
======================== 15 passed in 1.5s ========================
```

---

## 📡 API Reference & Usage Examples

### 1. Submit Bulk Certificate Generation Request
- **Endpoint:** `POST /api/v1/jobs`
- **Status Code:** `202 Accepted`

#### Request Body (`application/json`):
```json
{
  "event_title": "Full-Stack AI Engineering Masterclass",
  "issuer_name": "Global Academy of Technology",
  "signatory_name": "Dr. Eleanor Vance",
  "signatory_title": "Director of Certification",
  "issue_date": "October 11, 2026",
  "template_theme": "classic_gold",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice.johnson@example.com",
      "metadata": { "grade": "Distinction", "hours": "40" }
    },
    {
      "name": "Bob Smith",
      "email": "bob.smith@example.com",
      "metadata": { "grade": "Merit", "hours": "40" }
    }
  ]
}
```

#### cURL Example:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "event_title": "Cloud Architecture Bootcamp",
       "issuer_name": "Tech Institute",
       "recipients": [
         {"name": "Carol Williams", "email": "carol@example.com", "metadata": {"grade": "Excellence"}}
       ]
     }'
```

#### Response (`202 Accepted`):
```json
{
  "job_id": "79ab4dd5-65cd-4256-ad72-ac04af70e9f3",
  "event_title": "Cloud Architecture Bootcamp",
  "status": "PENDING",
  "total_recipients": 1,
  "message": "Bulk certificate generation job accepted and processing in background.",
  "status_url": "/api/v1/jobs/79ab4dd5-65cd-4256-ad72-ac04af70e9f3"
}
```

---

### 2. Check Job Status & Progress
- **Endpoint:** `GET /api/v1/jobs/{job_id}`
- **Status Code:** `200 OK`

#### Response:
```json
{
  "job_id": "79ab4dd5-65cd-4256-ad72-ac04af70e9f3",
  "event_title": "Cloud Architecture Bootcamp",
  "issuer_name": "Tech Institute",
  "signatory_name": "Dr. Eleanor Vance",
  "signatory_title": "Director of Certification",
  "issue_date": "October 11, 2026",
  "template_theme": "classic_gold",
  "status": "COMPLETED",
  "total_recipients": 1,
  "processed_count": 1,
  "success_count": 1,
  "failure_count": 0,
  "progress_percentage": 100.0,
  "zip_download_url": "/api/v1/jobs/79ab4dd5-65cd-4256-ad72-ac04af70e9f3/download-zip",
  "created_at": "2026-10-11T07:56:32.482000Z",
  "updated_at": "2026-10-11T07:56:33.112000Z",
  "completed_at": "2026-10-11T07:56:33.112000Z",
  "certificates": [
    {
      "id": "508c4448-823c-4300-9ab4-b6d9319df5b1",
      "recipient_name": "Carol Williams",
      "recipient_email": "carol@example.com",
      "status": "SUCCESS",
      "metadata": { "grade": "Excellence" },
      "download_url": "/api/v1/certificates/508c4448-823c-4300-9ab4-b6d9319df5b1/download",
      "preview_url": "/api/v1/certificates/508c4448-823c-4300-9ab4-b6d9319df5b1/preview",
      "verification_url": "/verify/508c4448-823c-4300-9ab4-b6d9319df5b1",
      "error_message": null,
      "created_at": "2026-10-11T07:56:32.482000Z",
      "generated_at": "2026-10-11T07:56:33.095000Z"
    }
  ]
}
```

---

### 3. Retrieve Generated Certificates

#### Download Individual PDF:
```bash
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/download"
```
Returns a PDF file named `{Recipient_Name}_Certificate.pdf`.

#### Inline Preview PDF:
```bash
http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/preview
```
Streams the PDF with `Content-Disposition: inline` for browser viewing.

#### Download All as ZIP:
```bash
curl -O -J "http://127.0.0.1:8000/api/v1/jobs/{job_id}/download-zip"
```
Bundles all successfully generated certificates in that job into a single `.zip` file.

---

### 4. Verify Certificate Authenticity

#### JSON API:
```bash
curl "http://127.0.0.1:8000/api/v1/verify/{certificate_id}"
```
```json
{
  "is_valid": true,
  "certificate_id": "508c4448-823c-4300-9ab4-b6d9319df5b1",
  "recipient_name": "Carol Williams",
  "recipient_email_masked": "c***l@example.com",
  "event_title": "Cloud Architecture Bootcamp",
  "issuer_name": "Tech Institute",
  "signatory_name": "Dr. Eleanor Vance",
  "signatory_title": "Director of Certification",
  "issue_date": "October 11, 2026",
  "status": "SUCCESS",
  "download_url": "/api/v1/certificates/508c4448-823c-4300-9ab4-b6d9319df5b1/download"
}
```

#### Public Web Page:
Navigate to `http://127.0.0.1:8000/verify/{certificate_id}` (embedded in the certificate's QR code) to view the verified credential badge.

---

## 💬 Interview Justifications & Discussion Points

| Design Decision | Solution Implemented | Why it was chosen | Production Alternative at 100k+ scale |
| :--- | :--- | :--- | :--- |
| **Concurrency / Worker** | FastAPI `BackgroundTasks` | Zero extra infra (no Redis/RabbitMQ setup required for local run), fully async HTTP lifecycle | Dedicated Celery/RQ workers with Redis broker & autoscaling container replicas |
| **Certificate PDF Rendering** | ReportLab Vector Engine | High visual fidelity, fast vector drawing, no headless browser overhead or security risks | Headless Chromium cluster if complex CSS grid/JS animations are required |
| **Database** | SQLite by default, SQLAlchemy ORM | Zero-configuration setup, instant test suite execution, atomic transactions | PostgreSQL with connection pooling (PgBouncer) & read replicas |
| **Storage** | Local disk storage (`storage/`) | Immediate read/write, simple path management | AWS S3 / Cloud Storage with pre-signed upload & download URLs |
| **Failure Isolation** | Per-recipient try-catch & DB status update | Guarantees that 1 bad recipient never ruins 999 good certificates | Dead Letter Queue (DLQ) for failed items with retry backoff |

---

## 📄 License
MIT License. Built for enterprise evaluation and technical assessment.
