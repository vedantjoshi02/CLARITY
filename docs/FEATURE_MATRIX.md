# Coverage of the CLARITY brief

| Brief section | Delivered behavior |
|---|---|
| 1–2: platform and objectives | Centralized student/admin application and academic resource preparation |
| 3: authentication | Required student fields, normalized unique email/enrollment, password matching/validation/hashing, separate admin login, terminal-created admins |
| 4: student dashboard | Personalized year, subject cards, resource counts, materials, papers, important questions, references, AI and profile navigation |
| 5: year-wise management | Four years/eight semesters, backend permission filtering including direct file URLs and AI |
| 6: admin dashboard | Dynamic student/year/subject/resource/query counts, recent students/resources, audit log |
| 7: student management | Year directory, name/enrollment/email search, profile, active/inactive controls, CSV, registration/last-login |
| 8: promotion | Confirmation, exactly one-year transition, fourth-year stop, immediate access refresh, retained identity and promotion history |
| 9: academics | Years, semesters, subject creation/editing and subject deletion with confirmation and resource protection |
| 10: resources | All eight categories, subject-derived year/semester, title, description, file, administrator review, publication and withdrawal, PDF/DOCX/PPTX validation and protected download |
| 11: AI assistant | Common subject selector; all eight task modes; 2/4/6/8/10 marks; model integration; sources; honest no-evidence/provider-failure behavior |
| 11: RAG pipeline | PDF/DOCX/PPTX extraction → overlapping chunks → text search and optional FAISS ranking → scoped retrieval → Gemini → source-linked answer |
| 12: profile | Name, email, enrollment, year, available semesters, registration, last login, promotion history; no student year editing |
| 13: AI management | Total queries, unique users, popular subjects, provider outcomes, processing status, recent indexed/failed docs, reprocess action |
| 14: technology | Django + SQLite + HTML/CSS + bundled Bootstrap + JavaScript + PyMuPDF + python-docx + FAISS |
| 15: database | All eleven proposed entities plus ActivityLog and RateLimit |
| 16: page structure | All 18 page purposes are present; semester view is a filter on subjects, year directory is a filter on students |
| 17–18: workflow | Runnable migration/setup/demo commands and integration tests for core transitions |
| 19: security | Hashing, uniqueness, backend role/year protection, upload limits, protected downloads, audit logs, confirmation and source references |
| Student enhancements | Saved and recently viewed resources, year notifications with read status, self-service student password reset, optional registration approval and domain allowlist |
| AI study enhancements | Subject-based multiple-choice quizzes and feedback, page-range PDF summarization, practice answer evaluation, optional local OCR for scans |
| Administration enhancements | Draft review queue, bulk uploads, year announcements, upload and download analytics, student activity and subject coverage |

## Explicit limits

- AI generation requires a Gemini API key and model configured in `.env`. Without it, the app returns labelled source excerpts.
- Live model calls were not exercised with credentials. Contract/error tests use mocked providers.
- Text search is available by default. Optional Gemini embeddings provide semantic ranking. Model answers and citations should be checked against the original material.
- Scanned PDF OCR requires Tesseract and installed language data. DOCX references use a section marker rather than a printed page number.
- Document preview is extracted text. Download the original to see original layout/figures.
- AI can describe appropriate diagrams in text; it does not generate graphical diagrams.
- Sample subjects are illustrative; there are no bundled authentic college PYQs.
