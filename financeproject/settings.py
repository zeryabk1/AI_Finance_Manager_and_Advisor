"""
Django settings for AI Finance Manager.
"""
import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller-built .exe. Bundled files (templates,
    # static, code) live in the temp extraction folder (_MEIPASS),
    # which is wiped/recreated on every launch — so the database and
    # media uploads must NOT live there, or they'd reset every run.
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'AIFinanceManager'
    DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR

# SECURITY WARNING: change this before deploying to production!
SECRET_KEY = 'django-insecure-CHANGE-THIS-SECRET-KEY-BEFORE-PRODUCTION'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ---------------------------------------------------------------
# Applications
# ---------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party
    'rest_framework',
    'rest_framework.authtoken',

    # local apps
    'accounts',
    'companies',
    'accounting',
    'transactions',
    'inventory',
    'assets',
    'reports',
    'dashboard',
    'api',
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

ROOT_URLCONF = 'financeproject.urls'

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

WSGI_APPLICATION = 'financeproject.wsgi.application'

# ---------------------------------------------------------------
# Database (SQLite3 - Django default, as required by spec)
# ---------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------
# Custom user model (accounts app) — gives us Role support
# ---------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------
# Email (used for password reset)
# ---------------------------------------------------------------
# Real Gmail SMTP account used to send password-reset links.
# NOTE: this is a plaintext credential sitting in source code.
# That's fine for local testing, but before this project goes
# anywhere public (GitHub, a shared server, production) move these
# two values back to environment variables / a secrets manager and
# rotate the app password below. See the note at the end of my
# reply for why.
EMAIL_HOST_USER = 'aifinancemanageradvisor@gmail.com'
EMAIL_HOST_PASSWORD = 'tgwpzfanhplmcwxf'  # Gmail App Password

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = f'AI Finance Manager <{EMAIL_HOST_USER}>'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
