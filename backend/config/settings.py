import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("DJANGO_SECRET_KEY", "django-insecure-medicare-cdss-key-change-in-prod"))
DEBUG = os.getenv("DEBUG", os.getenv("DJANGO_DEBUG", "True")).lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")).split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.accounts",
    "apps.patients",
    "apps.doctors",
    "apps.appointments",
    "apps.medical_records",
    "apps.predictions",
    "apps.medicines",
    "apps.assistant",
    "apps.audit_logs",
    "apps.admin_panel",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -------------------------------------------------------------------------
# Database Configuration
# Primary: PostgreSQL 16.x as mandated by MediCare SRS.
# SQLite is ONLY permitted when explicitly requested via USE_SQLITE_TESTS=true
# -------------------------------------------------------------------------
USE_SQLITE_TESTS = os.getenv("USE_SQLITE_TESTS", "false").lower() == "true"

if USE_SQLITE_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }
else:
    db_name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB"))
    db_user = os.getenv("DB_USER", os.getenv("POSTGRES_USER"))
    db_password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD"))
    db_host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
    db_port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))

    missing_db_vars = []
    if not db_name:
        missing_db_vars.append("DB_NAME (or POSTGRES_DB)")
    if not db_user:
        missing_db_vars.append("DB_USER (or POSTGRES_USER)")
    if db_password is None:
        missing_db_vars.append("DB_PASSWORD (or POSTGRES_PASSWORD)")

    if missing_db_vars:
        raise ImproperlyConfigured(
            f"PostgreSQL configuration error: Missing required database environment variables: {', '.join(missing_db_vars)}. "
            "Configure them in your .env file or set USE_SQLITE_TESTS=true explicitly for isolated test execution."
        )

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
            "OPTIONS": {
                "sslmode": os.getenv("DB_SSLMODE", "require"),
            },
            "TEST": {
                "NAME": db_name,
            },
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "medicare-default-cache",
    }
}

AUTH_USER_MODEL = "accounts.User"

if "pytest" in sys.modules or "test" in sys.argv or any("pytest" in arg for arg in sys.argv):
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
]

env_cors = [x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if x.strip()]
CORS_ALLOWED_ORIGINS = list(dict.fromkeys([
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    *env_cors,
]))
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS))

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

if not DEBUG:
    if SECRET_KEY == "django-insecure-medicare-cdss-key-change-in-prod":
        raise ImproperlyConfigured("SECRET_KEY must be configured with a secure production key when DEBUG is False.")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
