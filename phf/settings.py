from pathlib import Path
import environ
import os

env = environ.Env(
    DEBUG=(bool, False),
    ENV_NAME=(str, 'prod')  # default prod
)

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
    'crispy_forms',
    'crispy_bootstrap5',
    'referential.apps.ReferentialConfig',
    'methodology.apps.MethodologyConfig',
    'production.apps.ProductionConfig'
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
            ],
        },
    },
]

WSGI_APPLICATION = 'phf.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL')
}
DATABASES['default']['ENGINE'] = 'mssql'
base_options = {
    'driver': env('DB_DRIVER', default='ODBC Driver 17 for SQL Server'),
    'connection_timeout': 30,
}
if DEBUG:
    base_options['extra_params'] = 'Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes'
else:
    base_options['extra_params'] = 'Encrypt=yes'

DATABASES['default']['OPTIONS'] = base_options

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
