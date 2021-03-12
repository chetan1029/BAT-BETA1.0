"""
Base settings to build other settings files upon.
"""
from datetime import timedelta
from pathlib import Path

import environ
from django.utils.translation import ugettext_lazy as _

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# bat/
APPS_DIR = ROOT_DIR / "bat"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]
# Specify which language do we want for our website
LANGUAGES = (("en", _("English")), ("sv", _("Swedish")))
# A boolean that specifies whether to display numbers using a thousand separator.
USE_THOUSAND_SEPARATOR = True
# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL", default="postgres:///bat")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.postgres",
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "rest_auth",
    "rest_auth.registration",
    # Country list with flag and country code
    "django_countries",
    # Currency and currency conversion
    "djmoney",
    # Django defender
    "defender",
    # Django Modified Preorder Tree Traversal
    "mptt",
    # Tagging Manager to model
    "taggit",
    # Django Invitation
    "invitations",
    # Django Role Permissions
    "rolepermissions",
    # Django Notifications
    "notifications",
    # Django Filter
    "django_filters",
    # Dry Rest Permissions
    "dry_rest_permissions",
    # API documentation
    "drf_yasg2",
    # model translation
    "modeltranslation",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    # store the periodic celery task schedule in the database
    "django_celery_beat",
]
LOCAL_APPS = [
    "bat.users.apps.UsersConfig",
    "bat.core.apps.CoreConfig",
    "bat.company.apps.CompanyConfig",
    "bat.setting.apps.SettingConfig",
    "bat.product.apps.ProductConfig",
    "bat.comments.apps.CommentsConfig",
    "bat.subscription.apps.SubscriptionConfig",
    "bat.market.apps.MarketConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "bat.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
# LOGIN_REDIRECT_URL = "users:"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    # Cors Middleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Django defender middleware for failed login.
    "defender.middleware.FailedLoginMiddleware",
    # timezone middleware
    "bat.setting.middleware.TimezoneMiddleware",
    # Account setup middleware to forward user to complete company profile.
    "bat.users.middleware.AccountSetupMiddleware",
    # forward user on member list to select member profile
    "bat.users.middleware.MemberProfileMiddleware",
    # Django defender middleware for failed login.
    "defender.middleware.FailedLoginMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "bat.utils.context_processors.settings_context",
            ],
        },
    }
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(Path(APPS_DIR / "fixtures")),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend

# EMAIL_BACKEND = env(
#     "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
# )
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""bat""", "chetan@volutz.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool(
    "DJANGO_ACCOUNT_ALLOW_REGISTRATION", True
)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "none"  # "mandatory"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "bat.users.adapters.AccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "bat.users.adapters.SocialAccountAdapter"

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        # "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
}

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/.*$"

# rest-auth
SITE_ID = 1
REST_USE_JWT = True

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "bat.users.serializers.RestAuthRegisterSerializer"
}
REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "bat.users.serializers.UserSerializer",
    "PASSWORD_RESET_SERIALIZER": "bat.users.serializers.PasswordSerializer",
}

# jwt
JWT_AUTH = {"JWT_EXPIRATION_DELTA": timedelta(seconds=36000)}

# Django Invitation
ACCOUNT_ADAPTER = "invitations.models.InvitationsAdapter"

# Django Role Permissions
ROLEPERMISSIONS_MODULE = "config.roles"

# Dajngo Invitation
# INVITATIONS_SIGNUP_REDIRECT = "accounts:signup"
INVITATIONS_GONE_ON_ACCEPT_ERROR = False
INVITATIONS_INVITATION_MODEL = "users.InvitationDetail"

# django-defender
DEFENDER_LOGIN_FAILURE_LIMIT = 3
DEFENDER_DISABLE_IP_LOCKOUT = True
DEFENDER_LOCKOUT_TEMPLATE = "user/lockout.html"

# Django Taggit
TAGGIT_CASE_INSENSITIVE = True

# Redis
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/1")

# Some Global Variable for app
STATUS_PRODUCT = env.bool("STATUS_PRODUCT", "Product")

# Email Setting
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="bat-beta1.0 <noreply@beta.thebatonline.com>",
)

# cors
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS").split(",")

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
    "USE_SESSION_AUTH": DEBUG,
}

FORGET_PASSWORD_PAGE_LINK = env("FORGET_PASSWORD_PAGE_LINK", default="")
INVITE_LINK = env("INVITE_LINK", default="")
EXISTING_INVITE_LINK = env("EXISTING_INVITE_LINK", default="")

VENDOR_EXISTING_INVITE_LINK = env("VENDOR_EXISTING_INVITE_LINK", default="")

VENDOR_DEFAULT_PASSWORD = env("VENDOR_DEFAULT_PASSWORD", default="")

MARKET_LIST_URI = env(
    "MARKET_LIST_URI")

# Amazon oauth

AMAZON_SELLER_CENTRAL_AUTHORIZE_URL = env(
    "AMAZON_SELLER_CENTRAL_AUTHORIZE_URL")

AMAZON_LWA_TOKEN_ENDPOINT = env(
    "AMAZON_LWA_TOKEN_ENDPOINT"
)

AMAZON_APPLICATION_ID = env("AMAZON_APPLICATION_ID")

LWA_CLIENT_ID = env("LWA_CLIENT_ID")
LWA_CLIENT_SECRET = env("LWA_CLIENT_SECRET")

# market

SELLING_REGIONS = {
    "us_east_1": {
        "name": "North America",
        "endpoint": "https://sellingpartnerapi-na.amazon.com",
        "auth_url": env("AMAZON_SELLER_CENTRAL_AUTHORIZE_URL"),
    },
    "eu_west_1": {
        "name": "Europe",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "auth_url": env("AMAZON_SELLER_CENTRAL_AUTHORIZE_URL_EUROPE"),
    },
    "us_west_2": {
        "name": "Far East",
        "endpoint": "https://sellingpartnerapi-fe.amazon.com",
        "auth_url": env("AMAZON_SELLER_CENTRAL_AUTHORIZE_URL"),
    }
}
