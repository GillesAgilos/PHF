from pathlib import Path
import environ
import os

import phf.context_processors

env = environ.Env(
    DEBUG=(bool, False),
    ENV_NAME=(str, 'prod')  # default prod
)

ENV_NAME = env('ENV_NAME')

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_auth_adfs',
    'simple_history',
    'phf.apps.PhfConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_select2',
    'referential.apps.ReferentialConfig',
    'production.apps.ProductionConfig',
    'batch.apps.BatchConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'phf.middleware.LoginRequiredMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'phf.urls'

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
                'phf.context_processors.export_env_name',
            ],
        },
    },
]

WSGI_APPLICATION = 'phf.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'driver': env('DB_DRIVER'),
            'extra_params': 'Encrypt=no;TrustServerCertificate=yes',
            'connection_timeout': 30,
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = (
    'django_auth_adfs.backend.AdfsAuthCodeBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Configuration Entra ID
AUTH_ADFS = {
    'AUDIENCE': env('AZURE_CLIENT_ID'),
    'CLIENT_ID': env('AZURE_CLIENT_ID'),
    'CLIENT_SECRET': env('AZURE_CLIENT_SECRET'),
    'TENANT_ID': env('AZURE_TENANT_ID'),
    'RELYING_PARTY_ID': env('AZURE_CLIENT_ID'),
    'CONFIG_RELOAD_INTERVAL': 1440,
    'LOGIN_EXEMPT_URLS': ['login'],
}

# https
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 900
SESSION_SAVE_EVERY_REQUEST = True
