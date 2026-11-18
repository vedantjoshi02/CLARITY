# Architecture and maintenance guide

## Request flow

Browser → Django session and CSRF middleware → role guard → academic-year-filtered queryset → template / protected download / retrieval service.

Server-rendered HTML keeps the frontend simple: there is no separate Node build, SPA token storage, or permissive cross-origin API. Forms carry CSRF tokens. JavaScript enhances menus, suggested questions, pending states, and copying answers; core CRUD works without it.

## Main files

| File | Responsibility |
|---|---|
| `config/settings.py` | Environment configuration, SQLite, authentication, secure cookies, private storage |
| `academy/models.py` | Users, profiles, academic structure, resources, chunks, chats, usage, promotions, audit and rate-limit records |
| `academy/forms.py` | Registration, password checks, PDF/DOCX/PPTX validation, academic/resource editing, assistant input |
| `academy/access.py` | Role checks and reusable authorized querysets |
| `academy/views.py` | Student/admin workflows, protected download, confirmation and CSV export |
| `academy/rag.py` | Extraction, text retrieval, optional Gemini embeddings with FAISS, and Gemini generation |
| `academy/urls.py` | Application route map |
| `academy/tests.py` | Integration, permissions, processing and provider contract tests |
| `academy/management/commands/seed_demo.py` | Idempotent academic setup and optional original sample docs |
| `academy/management/commands/reindex_resources.py` | Rebuild extraction and embeddings |
| `templates/` | Accessible server-rendered pages and shared components |
| `static/css/app.css` | Custom responsive visual system |
| `static/css/bootstrap.min.css` | Locally bundled Bootstrap 5.3.3, MIT licensed |
| `static/js/app.js` | Menu, active navigation, prompt buttons, copy and submission states |

## Database relationships

| Entity | Relationships / purpose |
|---|---|
| User | Django AbstractUser; unique case-insensitive email; no plaintext passwords |
| StudentProfile | One-to-one User, unique normalized enrollment, current AcademicYear |
| AcademicYear | Four rows, one to many Semesters and Students |
| Semester | Eight rows, validated mapping to AcademicYear |
| Subject | Semester; code, name, description |
| Resource | Subject, uploader; private file and approval/status |
| DocumentChunk | Resource; page, position, text, optional semantic embedding |
| ChatHistory | User, Subject, marks, mode, question, answer, sources, timestamp |
| AIUsage | One-to-one ChatHistory; provider/outcome and elapsed milliseconds |
| PromotionHistory | Student, old/new years, actor, timestamp |
| ActivityLog | Administrative actor, action and timestamp |
| RateLimit | Hashed request bucket key, counter and expiration |

## Routes

| Route | Purpose / allowed users |
|---|---|
| `/` | Public home |
| `/register/`, `/login/` | Student registration / email login |
| `/admin-login/` | Admin username login |
| `/logout/` | POST logout |
| `/dashboard/` | Student summary; administrators redirect to manage |
| `/subjects/`, `/subjects/<id>/` | Semester/subject selection and scoped resources |
| `/resources/`, `/resources/<id>/` | Filtered library and resource details |
| `/resources/<id>/download/` | Authenticated and year-authorized attachment |
| `/profile/` | Read-only student profile |
| `/assistant/` | GET history, POST a scoped question |
| `/manage/` | Admin summary |
| `/manage/students/` | Directory and filtered `?export=csv` |
| `/manage/students/<id>/` | Student details |
| `/manage/students/<id>/<action>/` | GET confirmation, POST promote/activate/deactivate |
| `/manage/academics/` | Academic hierarchy |
| `/manage/academics/<kind>/new/` | Add a subject to a selected semester |
| `/manage/academics/<kind>/<id>/` | Edit academic item |
| `/manage/academics/<kind>/<id>/delete/` | Confirm and delete a subject |
| `/manage/resources/new/` | Upload |
| `/manage/resources/<id>/edit/` | Replace file, edit metadata or approve/unpublish |
| `/manage/resources/<id>/<action>/` | Delete/reindex confirmation and POST action |
| `/manage/ai/` | Usage and document health |
| `/system-admin/` | Django system administration; trusted superusers only |

## Important implementation decisions

- User-selected academic year at registration follows the supplied brief. It is not verification of college membership. Add enrollment verification if the institution needs it.
- The administrator cannot read plaintext passwords. The Django system interface retains normal trusted superuser account-maintenance powers.
- Only superusers reach custom management views. Generic Django admin does not expose academic mutations; use the application's validated forms for those.
- File extensions, PDF signatures, DOCX structure/expanded size, file size, extracted text and page counts are checked. This is not antivirus scanning.
- All files are attachment downloads after authorization, with private/no-store headers and `nosniff`; no public media route is installed.
- Retrieval rechecks year and subject and includes only approved/ready resources. History from previous years is hidden after promotion; history referencing withdrawn sources is redacted on display.
- The current year is looked up afresh from the profile for each request. A promotion audit is written in the same transaction as a conditional year update.
- Deactivation uses Django's `is_active`, which also prevents existing sessions from authenticating on subsequent requests.
- No background job runner is necessary for this mini-project. Large ingestion and large retrieval sets can block a request; add background processing and durable indexes when scaling.
- Rate limits use the direct client IP (login/registration) and user ID (AI), not an untrusted forwarded header. Configure a trusted proxy-aware policy for a production reverse proxy. Expired bucket rows can be pruned as maintenance.
