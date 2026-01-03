"""
Django settings for leakfix project.

This configuration is tuned for our referral‑leakage analytics MVP.  It reads
environment variables from a `.env` file for secrets and toggles, sets up
PostgreSQL/SQLite (depending on environment), and adds our `analytics` app.

We avoid storing personally identifiable information (PHI) by default.  The
`Patient` model in the `analytics` app stores only hashed identifiers.  Any
additional sensitive fields should be encrypted at rest.

For more information on these settings, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment reader and read from `.env` file if it exists.
env = environ.Env(
    DEBUG=(bool, False),
    PRODUCTION=(bool, False),
    SECRET_KEY=(str, 'change-me'),
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
    ATHENA_CLIENT_ID=(str, ''),
    ATHENA_CLIENT_SECRET=(str, ''),
    ALLOWED_HOSTS=(list, []),
    FIELD_ENCRYPTION_KEY=(str, ''),
)
environ.Env.read_env(str(BASE_DIR / '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')
PRODUCTION = env('PRODUCTION')

ALLOWED_HOSTS: list[str] = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Security settings for production environments
if PRODUCTION:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Encryption key for django-encrypted-model-fields
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'encrypted_model_fields',
    # Local apps
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'analytics.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'leakfix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'leakfix.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
#
# Uses dj-database-url to parse the DATABASE_URL environment variable.
# See https://github.com/jazzband/dj-database-url
DATABASES = {
    'default': env.db(),
}

# Enforce SSL for PostgreSQL connections in production.
if PRODUCTION and DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Caching configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table', # Unique name for the cache table
        'TIMEOUT': 300, # Cache for 5 minutes (300 seconds)
    }
}

# Use cached database sessions for better concurrency handling
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Login configuration: redirect users to the login page and then to the dashboard
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/analytics/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

ATHENA_CLIENT_ID = env('ATHENA_CLIENT_ID')
ATHENA_CLIENT_SECRET = env('ATHENA_CLIENT_SECRET')
