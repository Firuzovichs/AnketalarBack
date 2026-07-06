from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-prod')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
# Android emulator host (10.0.2.2 = Mac localhost from emulator)
if '10.0.2.2' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS += ['10.0.2.2', '10.0.2.15','45.138.159.86']

DJANGO_APPS = [
    'jazzmin',                          # Jazzmin birinchi bo'lishi shart
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'channels',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.users',
    'apps.locations',
    'apps.matches',
    'apps.stories',
    'apps.chat',
    'apps.notifications',
    'apps.subscriptions',
    'apps.search',
    'apps.home',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ── Database ──────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='anketalar_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ── Auth ──────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('REFRESH_TOKEN_LIFETIME_DAYS', default=30, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── Channels (WebSocket) ──────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [config('REDIS_URL', default='redis://localhost:6379/0')]},
    }
}

# ── Celery ────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ── Cache ─────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
    }
}

# ── Media / Static ────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')

# ── i18n ──────────────────────────────────────────────────────────
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS ──────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG

# ── API Docs ──────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Anketalar API',
    'DESCRIPTION': 'Anketalar Dating App Backend API',
    'VERSION': '1.0.0',
}

# ── App settings ──────────────────────────────────────────────────
OTP_EXPIRE_MINUTES = 5
STORY_EXPIRE_HOURS = 24
MAX_USER_PHOTOS = 5
FCM_SERVER_KEY = config('FCM_SERVER_KEY', default='')

# ── Apple In-App Purchase (StoreKit) ───────────────────────────────
# iOS ilovaning bundle ID'si — App Store Server Library xaridlarni shu
# bundle uchun ekanini tekshirishda ishlatadi (PRODUCT_BUNDLE_IDENTIFIER,
# anketalarr.xcodeproj/project.pbxproj).
APPLE_BUNDLE_ID = config('APPLE_BUNDLE_ID', default='com.shoxijaxon.anketalarr')
# "Sandbox" (TestFlight/dev) yoki "Production". App Store Connect'da haqiqiy
# mahsulotlar yaratilib, ilova chiqarilganda PRODUCTION'ga o'tkaziladi.
APPLE_ENVIRONMENT = config('APPLE_ENVIRONMENT', default='Sandbox')
# Faqat Production muhitida shart — App Store Connect'dagi ilova ID raqami.
_apple_app_apple_id_raw = config('APPLE_APP_APPLE_ID', default='')
APPLE_APP_APPLE_ID = int(_apple_app_apple_id_raw) if _apple_app_apple_id_raw else None
# Apple ildiz sertifikatlari shu papkada saqlanadi (.cer fayllar) —
# SignedDataVerifier shularsiz imzoni tekshira olmaydi.
APPLE_ROOT_CERTS_DIR = BASE_DIR / 'apple_certificates'

# ── Jazzmin (Admin Panel) ─────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "Anketalar Admin",
    "site_header": "Anketalar",
    "site_brand": "Anketalar",
    "site_logo": None,
    "welcome_sign": "Anketalar boshqaruv paneliga xush kelibsiz",
    "copyright": "Anketalar © 2025",
    "search_model": ["users.User"],
    "topmenu_links": [
        {"name": "Bosh sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/docs/", "new_window": True},
    ],
    "usermenu_links": [
        {"name": "API Docs", "url": "/api/docs/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "users.User": "fas fa-user",
        "users.UserProfile": "fas fa-id-card",
        "users.UserPhoto": "fas fa-image",
        "users.Interest": "fas fa-heart",
        "users.Goal": "fas fa-bullseye",
        "matches.Like": "fas fa-thumbs-up",
        "matches.Match": "fas fa-handshake",
        "stories.Story": "fas fa-film",
        "chat.ChatRoom": "fas fa-comments",
        "chat.Message": "fas fa-envelope",
        "notifications.Notification": "fas fa-bell",
        "subscriptions.Plan": "fas fa-gem",
        "subscriptions.UserSubscription": "fas fa-crown",
        "locations.Country": "fas fa-globe",
        "locations.Region": "fas fa-map",
        "locations.District": "fas fa-map-marker-alt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-danger",
    "accent": "accent-danger",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-danger",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
