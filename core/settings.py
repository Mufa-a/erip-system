from pathlib import Path
from decouple import config
import sentry_sdk

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG      = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Security
    'axes',
    # Our ERP apps
    'accounts',
    'core',
    'customers',
    'products',
    'sales',
    'inventory',
    'payments',
    'suppliers',
    'reports',
    'hr',
    'company',
    'billing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'company.middleware.CompanyMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='erp_db'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
        'CONN_MAX_AGE': 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Nairobi'
USE_I18N      = True
USE_TZ        = True

STATIC_URL   = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL    = '/media/'
MEDIA_ROOT   = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ============================================================
# 📝 MESSAGE TAGS
# ============================================================
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR:   'error',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.INFO:    'info',
}

# ============================================================
# 🔒 SECURITY SETTINGS
# ============================================================
SECURE_BROWSER_XSS_FILTER    = True
SECURE_CONTENT_TYPE_NOSNIFF  = True
X_FRAME_OPTIONS              = 'DENY'
SECURE_REFERRER_POLICY       = 'strict-origin-when-cross-origin'

if not DEBUG:
    SECURE_SSL_REDIRECT            = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True

SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_AGE              = 28800  # 8 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_HTTPONLY            = True

# ============================================================
# 🚫 RATE LIMITING — django-axes
# ============================================================
AXES_FAILURE_LIMIT      = 5
AXES_COOLOFF_TIME       = 1
AXES_LOCKOUT_TEMPLATE   = 'lockout.html'
AXES_RESET_ON_SUCCESS   = True
AXES_ENABLE_ADMIN       = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ============================================================
# 📧 EMAIL
# ============================================================
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST',          default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',          default=587, cast=int)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS       = config('EMAIL_USE_TLS',       default=True, cast=bool)
DEFAULT_FROM_EMAIL  = config('EMAIL_HOST_USER',     default='noreply@erip.com')

# ============================================================
# 📱 M-PESA
# ============================================================
MPESA_CONSUMER_KEY    = config('MPESA_CONSUMER_KEY',    default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE       = config('MPESA_SHORTCODE',       default='174379')
MPESA_PASSKEY         = config('MPESA_PASSKEY',         default='')
MPESA_CALLBACK_URL    = config('MPESA_CALLBACK_URL',    default='')
MPESA_ENV             = config('MPESA_ENV',             default='sandbox')

# ============================================================
# 📱 AFRICA'S TALKING SMS
# ============================================================
AT_USERNAME = config('AT_USERNAME', default='sandbox')
AT_API_KEY  = config('AT_API_KEY',  default='')

# ============================================================
# 📊 ERROR TRACKING — Sentry
# ============================================================
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

# ============================================================
# 📝 LOGGING
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/erp.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/security.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'erp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}