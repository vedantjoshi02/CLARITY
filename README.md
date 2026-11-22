# CLARITY

**AI-powered academic resources and examination preparation.**

A runnable Python full-stack mini-project based on the supplied CLARITY brief: Django, SQLite, server-rendered HTML, locally bundled Bootstrap, custom responsive CSS, and JavaScript. The interface uses warm ivory, forest green, soft subject colors, a student workspace, and a separate administrator workspace.

## Quick start — Windows / PowerShell

Install **standard 64-bit Python 3.14.2**. Extract this archive and open PowerShell inside the `clarity` folder.

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Setup installs the dependencies, creates SQLite tables, prepares four years and eight semesters, asks you to create an administrator, and adds original sample documents. It creates no default student or administrator passwords. Setup can be rerun: it reuses an existing administrator and preserves `.env`, `db.sqlite3`, and uploaded resources. An incompatible old `.venv` is renamed to a backup before a fresh Python 3.14 environment is created.

Open **http://127.0.0.1:8000**. Register a student in **Second Year** to explore the included Data Structures and Operating Systems resources. Admin sign-in uses the username you supplied to `createsuperuser`; student sign-in uses email.

### Upgrading an existing CLARITY installation

Stop the running server and deactivate the old virtual environment. Copy the updated project files into your existing project folder, keeping your `.env`, `db.sqlite3`, and `private_media` folder. Back up SQLite and uploaded files, then run `setup.ps1` to apply pending migrations, including `academy.0003_subject_only` before starting `run.ps1`. Migration `academy.0003_subject_only` removes legacy unit definitions and assignments. Uploaded files and their subject assignments are preserved. Do not reuse a Python 3.12/3.13 virtual environment with Python 3.14. The setup script preserves the old environment in `.venv-backup-<unique-id>`; it does not reset application data.

This package targets regular CPython 3.14, 64-bit x86 Windows (not the experimental free-threaded build). Python 3.14.2 was tested directly on Linux; all Windows x64 dependency wheels were downloaded successfully, but the Windows scripts were not executed on a Windows machine.

### Manual setup (fresh installation)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py seed_demo --resources
.\.venv\Scripts\python.exe manage.py runserver
```

For Linux/macOS, use `python3.14 -m venv .venv`, `.venv/bin/python`, and `cp .env.example .env` in the corresponding steps. A Python 3.14.2 64-bit environment is the tested baseline; Dependencies are pinned to the versions verified for this release. Windows timezone data is included explicitly.

## What works

- Separate public student registration, email login, and administrator username login.
- Unique normalized emails/enrollment numbers, Django password hashing/validation, CSRF protection, POST logout, and database-backed request limits.
- Four academic years, eight semesters, editable year labels, and subjects.
- Personalized student dashboard, semester and subject views, library filters, search, pagination, and profile information.
- All eight resource categories: notes, previous-year papers, class tests, reference books, important questions, question banks, syllabi, other materials.
- PDF/DOCX/PPTX upload and replacement, 20 MB limit, signature/archive validation, approval/draft visibility, original downloads, and extracted-text previews.
- Year-based authorization on subjects, files, downloads, AI retrieval, and chat history. Private files have no public media route.
- Student directory by year, search, profile, activation/deactivation, CSV export, and registration/last-login details.
- Confirmed manual promotions, fourth-year stop, replay protection, audit trail, and immediate change of academic access.
- Document extraction, page-aware PDF chunks, text search and optional Gemini embeddings with FAISS, document status, and reindexing.
- AI task choices: exam answer, concept explanation, short notes, comparison, previous-year solution, important points, diagram suggestions, technical terminology.
- 2/4/6/8/10-mark instructions, supporting source links, insufficient-evidence response, private question history, and usage statistics.
- Admin overview, recent registrations/uploads, popular subjects, response outcomes, document health, and activity log.

See `docs/FEATURE_MATRIX.md` for requirement-to-implementation mapping and `docs/ARCHITECTURE.md` for models, routes, and security boundaries.

## Study and administration tools

- **My Library** shows saved documents and recent resource activity, including opened and downloaded items. The dashboard shows previews of both lists.
- **Notifications** lists new publications and announcements for the student's current year. Administrators can send year-specific announcements from **Manage → Announcements**.
- **AI study tools** are available from the study companion. Quizzes use approved indexed material for the selected subject. A summary uses the selected PDF's indexed pages. For long PDFs, choose a smaller page range. Answer evaluation gives practice feedback and uses matching approved excerpts when available. These features use the same Gemini model and hourly request limit as the assistant.
- **Resource review** lists drafts. Single uploads are extracted when saved. Bulk uploads accept up to ten files sharing one classification and start as pending drafts. Open a draft and choose **Reprocess document** to extract its text, then **Approve and publish**. Published resources can return to the queue. Replacing a file or changing its subject requires review again. An inaccessible text preview does not stop an administrator from reviewing the original file and publishing it after extraction has been attempted.
- **Analytics** shows upload counts by day and type, subject coverage, recorded student downloads and seven-day student activity. View and download tracking begins when the upgrade is installed.

## Password reset and registration

The student sign-in page includes **Forgot password?**. The development email backend prints reset links in the Django terminal. For real delivery, set `PUBLIC_BASE_URL` to the trusted HTTPS origin and configure the SMTP settings in `.env.example`. Reset links expire after one hour.

Set `STUDENT_APPROVAL_REQUIRED=true` to hold new registrations until an administrator verifies enrollment and academic year and selects **Activate** in the student directory. Optionally set `STUDENT_EMAIL_DOMAINS` to a comma-separated list of allowed institutional domains. The domain check validates the address format and domain. Administrative review verifies enrollment.

## Enable Gemini answers

In your project folder, keep or create a local `.env` and set:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
LLM_MODEL=gemini-3.5-flash-lite
AI_SEMANTIC_RETRIEVAL=false
```

Restart Django. With a working Gemini key and available model quota, ask a question such as
“Explain the four necessary conditions for deadlock” under Operating Systems for 6 marks.
The assistant uses approved passages when they match. When nothing matches, general academic
questions still get a Gemini answer with a general-knowledge label. Questions explicitly
asking about uploaded material require matching passages. In disabled mode, matching text
is shown as excerpts. Gemini errors are displayed with a short diagnostic and any matching excerpts.

### Recover files from an older installation

Stop Django and copy the updated project files into the existing directory. Keep your local
`.env`, `db.sqlite3`, and `private_media/`. Check the Gemini settings above, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py reindex_resources
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Reindexing rebuilds searchable text from PDF, DOCX and PPTX files. For scanned PDFs, install **Tesseract OCR** and the required language packs. Add it to PATH or set `TESSERACT_COMMAND` to the executable path. English (`eng`) is the default. Set `OCR_LANGUAGES` to the installed language codes, such as `eng+mar`. New PDFs use OCR automatically on pages with images and little embedded text. Reindex previously uploaded scans after installing Tesseract. OCR is limited to 40 pages and 90 seconds per document. Split larger scans into smaller files. Recognition quality varies, especially for handwriting. Text search works independently of your Gemini embedding quota.
Set `AI_SEMANTIC_RETRIEVAL=true` and reindex if you want to enable semantic ranking alongside
text search. Keep the embedding model and dimensions consistent across indexing and retrieval.
Gemini receives the question or practice answer and the selected approved material needed for that request.

## Demonstrate the project

1. Create an admin through `createsuperuser`; never expose public admin registration.
2. Register a second-year student using any valid test email and a strong password.
3. Browse Data Structures, open “Arrays & linked lists: a comparison,” and download the DOCX.
4. Ask “Explain the four necessary conditions for deadlock” under Operating Systems, 6 marks.
5. In default mode, verify the labelled excerpts and source links. Configure a provider to demonstrate generation.
6. Sign in as admin, upload a PDF with text, and check its indexing status in AI management.
7. Promote the student with confirmation. On their next request, only third-year materials are accessible; old resource URLs fail.
8. Deactivate the account; an existing student session loses access. Reactivate it to permit login.

The sample subjects/semester placement are illustrative. Change them to match your approved college syllabus. Sample documents are original demonstration material. No official previous-year papers or copyrighted reference books are bundled.

## Tests

```powershell
.\.venv\Scripts\python.exe manage.py test academy
.\.venv\Scripts\python.exe manage.py check
```

The suite covers registration, roles, template routes, cross-year access, drafts, promotion replay, deactivation, CSV safety, PDF/DOCX/PPTX handling, replacement and deletion, retrieval scope, history privacy, mocked provider behavior, CSRF, CRUD, and throttling. See `docs/TEST_REPORT.md` for the recorded results.

## Data and maintenance

- `db.sqlite3`: users, sessions, academic metadata, chunks/embeddings, history, usage, audit logs.
- `private_media/documents/`: uploaded originals stored under random filenames.
- `.env`: secret configuration; excluded from the deliverable and source control.
- `python manage.py reindex_resources`: rebuild chunks from uploaded documents.
- Back up SQLite and private files together. Do not serve `private_media` directly from a web server.
- Subject removal is blocked while resources refer to it.
- Structural year/semester numbers cannot be reassigned through edit forms, preserving the four-year access model.
- Academic year changes use administrator controls. For institutional deployment, enable the registration review policy above. A trusted administrator can also reset a password using `python manage.py changepassword USERNAME`.

## Deployment

This is a **Python/Django project**, delivered as source rather than a static site. Use a host with a Python process and persistent filesystem/database support. The supplied `runserver` command is for development, not public production.

For a production deployment: use a WSGI server (for example a Linux Gunicorn deployment), HTTPS, a unique secret, `DEBUG=false`, explicit `ALLOWED_HOSTS`, `collectstatic`, and private persistent storage. Configure upload request limits at the reverse proxy and schedule backups. Run `manage.py check --deploy`; configure secure proxy headers only for your trusted proxy. A deployment without persistent disk will lose SQLite and files. A multi-worker/multi-host deployment should use PostgreSQL and private object storage and replace synchronous indexing with a worker queue.

Django security reference used during implementation: https://docs.djangoproject.com/en/5.2/topics/security/

## Admin academic and resource workflow

- Open **Manage → Academic structure**, select an academic year, then select one of its two semesters. Add, edit, or remove subjects from that selected semester. The standard four-year/eight-semester structure is initialized with `python manage.py seed_demo`; admins do not need to create years and semesters one by one.
- Supported uploads are PDF, DOCX, legacy PPT, and PPTX (up to 20 MB). PDF, DOCX, and PPTX text is extracted for the on-page preview and AI retrieval. Legacy `.ppt` files can be downloaded, but must be saved as `.pptx` to enable slide text preview and AI retrieval.
- Install the added PowerPoint parser dependency with `pip install -r requirements.txt`.

## Online reader, past-paper frequency, and updated quizzes

- **Read online** is available in the resource list and on resource details. PDFs use the browser's PDF viewer. DOCX files display paragraphs, headings, tables and supported embedded images. PPTX files open one slide at a time with text, tables and supported images. Office previews simplify layout and may omit charts, animations and media. Students can still download the original when they need its full formatting. Readers follow the same publication and academic-year access rules as downloads.
- **Past paper frequency** is available on subject resource pages, the previous-year papers list, and under AI study tools. Upload each exam as a separate resource, choose **Previous-year papers**, assign its subject, and publish it after indexing. Scans with incomplete extraction may need OCR and reindexing. Clarity looks at up to six distinct indexed files within a 36,000-character budget, prioritizing recent uploads. It shows the files checked, quoted evidence and one count per matching file. AI groups related wording. Counts describe the available historical papers and do not predict future papers.
- **AI quizzes** can focus on a topic selected from the paper rankings or sample across approved indexed teaching material and use separate instructions for recall, application and multi-step reasoning. Each question needs four distinct choices, one keyed answer and a supporting quote that matches the cited excerpt. Answer choices are shuffled. Explanations and quoted evidence appear after grading. If the selected material is too thin, try a smaller quiz or upload more teaching material.

The AI features require the same Gemini configuration as the existing assistant. This update adds no database migration or Office server dependency. On Render, keep the existing database connection and persistent private media settings when deploying the source. A fresh local development setup defaults to SQLite when no `DATABASE_URL` is set. The distribution ZIP contains source files and example settings. Keep your existing environment settings, database and uploaded resources with your installation.
