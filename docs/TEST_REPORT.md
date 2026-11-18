# Verification report

Executed on 12 November 2026 in Python 3.12 with Django 5.2.19.

- Django system check: passed, no issues.
- Initial schema migrations: applied successfully to a fresh SQLite database.
- Automated suite: 27 tests passed.
- Both PDF and DOCX processing and the FAISS path exercised with real documents.
- Model integration: request structure and timeout behavior verified with mocks. A live model was not configured.

Test coverage includes public/student/admin routes; registration and normalized uniqueness; separate logins; role enforcement; direct cross-year resource/download denial; draft invisibility; promotion access changes and replay prevention; fourth-year boundary; deactivation of active sessions; CSV filtering/formula handling; malformed/oversized files; upload/replace/reindex/delete; PDF extraction; empty document status; retrieval permissions; no-evidence response; assistant persistence; chat privacy and withdrawn citations; marks/source provider prompt; provider failure; CSRF and safe GET behavior; semester consistency; academic CRUD; request limiting.

Browser verification findings are recorded below after the visual review. The archive excludes the preview database, preview identities, `.env`, cached files and development virtual environment.

Visual review: the live public home and server-rendered student dashboard/assistant fixtures were inspected in the cloud browser. The dashboard was also inspected in a 390-pixel iframe viewport. No clipping or horizontal layout overflow was visible in the inspected views. Authenticated workflows were exercised by the Django test client, not by a live browser sign-in. Browser fixtures are not shipped.

## Python 3.14.2 compatibility update

- Installed CPython 3.14.2 in a fresh Linux virtual environment and installed the full dependency set.
- Re-ran all 27 tests: passed, including real PDF/DOCX processing and FAISS retrieval.
- Django checks: no issues; migration drift check: no changes.
- Downloaded all dependencies as binary wheels targeting CPython 3.14, Windows x86-64. This verifies package availability, not native Windows execution.
- Updated PowerShell setup/run commands for Python 3.14.2+ (3.14 series), with environment validation, old-environment backup, explicit timezone data and repeatable admin detection. Windows/PowerShell execution remains untested here.

## Gemini assistant repair

All 31 Django tests passed on CPython 3.14.2. They exercise the answer form, general
answers without sources, source-specific questions, provider quota errors, optional
embedding failures, and retry after the model reaches its output-token limit.
The Gemini SDK request and response were checked against a local HTTP fixture.
A live Gemini request with a real key was not run.

Reindexing a temporary copy of the supplied database and uploads recovered 2,156 text
chunks from one PDF. The second PDF needs OCR. No schema migrations were required.

## Enhancement release verification

The 39-test suite passed on Linux with Python 3.12 and Django 5.2.19. Eight integration tests cover private and year-scoped resource activity, review and notifications, bulk validation, reset-token use, optional signup approval, quiz scoring, summary and answer evaluation, and a real image-only PDF OCR pass using Tesseract. Gemini and outgoing email use test doubles or Django's in-memory email backend. The Windows installer and live Gemini and SMTP services were not exercised for this release.

## Subject-only release verification

All 40 Django tests passed. Regression checks cover subject-only resource forms, the former unit endpoint, quiz generation from multiple approved materials for one subject, cross-year and unpublished resource exclusion, and grading a quiz created before the migration. The bundled SQLite database was migrated and compared with the previous release. Existing records and subject assignments were preserved, and the legacy unit schema and permissions were removed.
