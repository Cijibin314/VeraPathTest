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
    SECRET_KEY=(str, 'change-me'),
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
    ATHENA_CLIENT_ID=(str, ''),
    ATHENA_CLIENT_SECRET=(str, ''),
)
environ.Env.read_env(str(BASE_DIR / '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS: list[str] = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

# Use DATABASE_URL from environment for flexibility.  Defaults to SQLite.
DATABASES = {
    'default': env.db(),
}

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
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300, # Cache for 5 minutes (300 seconds)
    }
}

# Login configuration: redirect users to the login page and then to the dashboard
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/analytics/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

ATHENA_CLIENT_ID = env('ATHENA_CLIENT_ID')
ATHENA_CLIENT_SECRET = env('ATHENA_CLIENT_SECRET')
