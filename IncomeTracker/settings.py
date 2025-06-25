from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------------------------
# FUNCTION TO READ .env FILE
# -------------------------------------------------------------------
def read_env_file(file_path: str) -> dict:
    """Reads a .env file and returns a dictionary of key-value pairs."""
    env_vars = {}
    try:
        with open(file_path) as f:
            for line in f:
                # Ignore comments and empty lines
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Split key and value
                key, value = line.split("=", 1)
                # Strip surrounding quotes (single or double)
                value = value.strip().strip("'").strip('"')
                env_vars[key.strip()] = value
    except FileNotFoundError:
        raise FileNotFoundError(f"Environment file not found: {file_path}")
    return env_vars


# Load environment variables from .env
env_file_path = BASE_DIR / ".env"
env = read_env_file(env_file_path)

# -------------------------------------------------------------------
# SECURITY SETTINGS
# -------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get("SECRET_KEY", "unsafe-default-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.get("DEBUG", "False") == "True"

# Allowed hosts
ALLOWED_HOSTS = env.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

# -------------------------------------------------------------------
# TWILIO SETTINGS
# -------------------------------------------------------------------
TWILIO_ACCOUNT_SID = env.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_TEMPLATE_SID = env.get("TWILIO_WHATSAPP_TEMPLATE_SID")
TWILIO_FROM_WHATSAPP_NUMBER = env.get("TWILIO_FROM_WHATSAPP_NUMBER")

# -------------------------------------------------------------------
# APPLICATION DEFINITION
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "django.contrib.humanize",
    "debug_toolbar",
    # Local apps
    "incomes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Third-party
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "IncomeTracker.urls"

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

WSGI_APPLICATION = "IncomeTracker.wsgi.application"

# -------------------------------------------------------------------
# DATABASE CONFIGURATION
# -------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC AND MEDIA FILES
# -------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # For development, points to ./static/
STATIC_ROOT = BASE_DIR / "staticfiles"  # For production, points to ./staticfiles/

# Media files (e.g., user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# -------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# LOGIN AND LOGOUT REDIRECT SETTINGS
# -------------------------------------------------------------------
LOGIN_URL = "/incomes/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/incomes/logged_out/"

# -------------------------------------------------------------------
# PRODUCTION SETTINGS (APPLIED ONLY WHEN DEBUG IS FALSE)
# -------------------------------------------------------------------
if not DEBUG:
    # Security settings
    SECURE_SSL_REDIRECT = True  # Redirect all HTTP traffic to HTTPS
    SESSION_COOKIE_SECURE = True  # Use secure cookies for sessions
    CSRF_COOKIE_SECURE = True  # Use secure cookies for CSRF
    SECURE_HSTS_SECONDS = 31536000  # Enforce HTTPS for 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to all subdomains
    SECURE_HSTS_PRELOAD = True  # Preload HSTS
    SECURE_BROWSER_XSS_FILTER = True  # Enable XSS filter in browsers
    SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Allowed hosts for production
    ALLOWED_HOSTS = env.get("ALLOWED_HOSTS", "").split(",")
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
        raise ValueError("ALLOWED_HOSTS must be set in production!")

    # Static and media files
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

    # Logging for production
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "file": {
                "level": "ERROR",
                "class": "logging.FileHandler",
                "filename": BASE_DIR / "logs/error.log",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level": "ERROR",
                "propagate": True,
            },
        },
    }

    # Override DB settings with PostgreSQL config
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env["POSTGRES_DB"],
        "USER": env["POSTGRES_USER"],
        "PASSWORD": env["POSTGRES_PASSWORD"],
        "HOST": env.get("POSTGRES_HOST", "localhost"),
        "PORT": env.get("POSTGRES_PORT", "5432"),
        "OPTIONS": {"options": "-c search_path=public"},
    }

    # Other production-specific settings can go here
