from pathlib import Path
import os

from dotenv import load_dotenv


# ==========================================================
# BASE DIRECTORY AND ENVIRONMENT
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)


# ==========================================================
# SECURITY
# ==========================================================

DEBUG = os.getenv("DEBUG", "true").lower() == "true"

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "local-development-only-change-before-deployment-clarity"
)

if not DEBUG and SECRET_KEY.startswith("local-development"):
    raise RuntimeError(
        "Set a private SECRET_KEY before deployment."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,testserver"
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    value.strip()
    for value in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if value.strip()
]


# ==========================================================
# INSTALLED APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "academy",
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# URL CONFIGURATION
# ==========================================================

ROOT_URLCONF = "config.urls"


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates"
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

                "academy.context.navigation",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# ==========================================================
# DATABASE
# ==========================================================

import dj_database_url

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            ssl_require=DATABASE_URL.startswith(("postgres:", "postgresql:")),
        )
    }
elif DEBUG:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    raise RuntimeError("Set DATABASE_URL before deployment.")


# ==========================================================
# CUSTOM USER MODEL
# ==========================================================

AUTH_USER_MODEL = "academy.User"


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },

    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",

        "OPTIONS": {
            "min_length": 10
        },
    },

    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },

    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC FILES
# ==========================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static"
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ==========================================================
# MEDIA FILES
# ==========================================================

# Uploaded academic resources are stored privately.
# Do not expose MEDIA_ROOT through a public URL.

MEDIA_ROOT = BASE_DIR / "private_media"


# ==========================================================
# DEFAULT PRIMARY KEY
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# AUTHENTICATION
# ==========================================================

LOGIN_URL = "/login/"

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# ==========================================================
# SECURITY SETTINGS
# ==========================================================

SECURE_SSL_REDIRECT = not DEBUG

SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"


# ==========================================================
# FILE UPLOAD LIMITS
# ==========================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 22 * 1024 * 1024

FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024


# ==========================================================
# CLARITY AI CONFIGURATION
# ==========================================================

# Supported provider:
# disabled = No AI generation
# gemini   = Google Gemini API

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "disabled"
).strip().lower()


# Gemini API key

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()


# Gemini generation model

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "gemini-3.5-flash-lite"
).strip()


# Gemini embedding model

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001"
).strip()


# Embedding dimensions

EMBEDDING_DIMENSION = int(
    os.getenv(
        "EMBEDDING_DIMENSION",
        "768"
    )
)


# Number of document chunks retrieved for an answer

AI_RETRIEVAL_TOP_K = int(
    os.getenv(
        "AI_RETRIEVAL_TOP_K",
        "6"
    )
)


# Minimum similarity score

AI_SIMILARITY_THRESHOLD = float(
    os.getenv(
        "AI_SIMILARITY_THRESHOLD",
        "0.45"
    )
)


# Maximum output tokens

AI_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "AI_MAX_OUTPUT_TOKENS",
        "1800"
    )
)


# ==========================================================
# LOGGING
# ==========================================================

# Print AI errors and tracebacks in the Django terminal.

LOGGING = {
    "version": 1,

    "disable_existing_loggers": False,

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },

    "loggers": {
        "academy.rag": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

AI_SEMANTIC_RETRIEVAL = os.getenv("AI_SEMANTIC_RETRIEVAL", "false").strip().lower() == "true"

# Student registration. Administrators verify enrollment and activate pending
# students from the existing student directory when approval is enabled.
STUDENT_APPROVAL_REQUIRED = os.getenv('STUDENT_APPROVAL_REQUIRED', 'false').lower() == 'true'
STUDENT_EMAIL_DOMAINS = {
    value.strip().lower() for value in os.getenv('STUDENT_EMAIL_DOMAINS', '').split(',') if value.strip()
}

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'CLARITY <no-reply@localhost>')
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '').rstrip('/')
PASSWORD_RESET_TIMEOUT = 60 * 60

OCR_ENABLED = os.getenv('OCR_ENABLED', 'true').lower() == 'true'
TESSERACT_COMMAND = os.getenv('TESSERACT_COMMAND', 'tesseract')
OCR_LANGUAGES = os.getenv('OCR_LANGUAGES', 'eng')
