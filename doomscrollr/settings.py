import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta
from django.core.management.utils import get_random_secret_key

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---
SECRET_KEY = os.getenv("SECRET_KEY", get_random_secret_key())
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# --- Installed Apps ---
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "dj_rest_auth",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    # ❌ REMOVED: "rest_framework.authtoken" - this was causing the token model conflict
    "rest_framework_simplejwt.token_blacklist", 
    # Local apps
    "projects",
]

SITE_ID = 1

# --- Middleware ---
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be first
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "doomscrollr.urls"

# --- Templates ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "doomscrollr.wsgi.application"

# --- Database ---
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# doomscrollr/settings.py (at the bottom of the file)
# ...

# --- Static & Media ---
STATIC_URL = "/static/"
# ✅ FIX: Explicitly define STATIC_ROOT for collecting static files in production
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- REST Framework & JWT ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # ✅ CHANGED: Use dj-rest-auth's JWT authentication class for better integration
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

# ✅ CRITICAL FIX: Properly configure dj-rest-auth to use JWT
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": None,  # We're using localStorage, not cookies
    "JWT_AUTH_REFRESH_COOKIE": None,
    "JWT_AUTH_HTTPONLY": False,
    "TOKEN_MODEL": None,  # ← This disables the legacy token model completely
}

# In settings.py, update SIMPLE_JWT:

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,  # ✅ Disable blacklist for now to debug
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "UPDATE_LAST_LOGIN": False,
}

# --- allauth / dj-rest-auth ---
ACCOUNT_AUTHENTICATION_METHOD = "username"  # ✅ Using correct setting name
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",  # ✅ Added allauth backend
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS / CSRF ---
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://doomscrollr.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.github\.dev$",
    r"^https://.*\.codespaces\.github\.io$",
    r"^https://.*\.preview\.app\.github\.dev$",  # ✅ Added for Codespaces previews
]
CSRF_TRUSTED_ORIGINS = [
    "https://doomscrollr.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ✅ ADDED: This was missing from your version!
# Disable legacy token model (we use JWT only)
REST_AUTH_TOKEN_MODEL = None