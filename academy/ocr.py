from math import isfinite
from shutil import which
from subprocess import PIPE, DEVNULL, SubprocessError, run
from time import monotonic

from django.conf import settings
from pymupdf import Matrix

MAX_OCR_PAGES = 40
OCR_BUDGET_SECONDS = 90
OCR_PAGE_TIMEOUT = 12


class PdfOcr:
    """Bound OCR work per document while preserving its original page numbers."""

    def __init__(self):
        self.command = which(settings.TESSERACT_COMMAND) if settings.OCR_ENABLED else None
        self.deadline = None
        self.attempts = 0
        self.skipped = 0
        self.unavailable = not self.command

    def extract(self, page):
        if self.deadline is None:
            self.deadline = monotonic() + OCR_BUDGET_SECONDS
        remaining = self.deadline - monotonic()
        if self.unavailable or self.attempts >= MAX_OCR_PAGES or remaining <= 0:
            self.skipped += 1
            return ''

        size = max(page.rect.width, page.rect.height)
        if not isfinite(size) or size <= 0:
            self.skipped += 1
            return ''
        self.attempts += 1
        try:
            scale = min(2.5, 2400 / size)
            image = page.get_pixmap(matrix=Matrix(scale, scale), alpha=False, annots=False)
            result = run(
                [self.command, 'stdin', 'stdout', '-l', settings.OCR_LANGUAGES],
                input=image.tobytes('png'), stdout=PIPE, stderr=DEVNULL,
                timeout=min(OCR_PAGE_TIMEOUT, remaining), check=False,
            )
            if result.returncode == 0:
                return result.stdout.decode('utf-8', errors='replace')
            self.unavailable = True
        except (OSError, SubprocessError, RuntimeError, ValueError):
            pass
        self.skipped += 1
        return ''

    @property
    def warning(self):
        if not self.skipped:
            return ''
        if self.unavailable:
            return 'Some scanned pages could not be read. Enable OCR, install Tesseract and its language data, then reindex.'
        return 'Some scanned pages could not be read within the OCR limits. Split large scans and reindex if needed.'
