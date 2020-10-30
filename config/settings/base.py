"""
Base settings to build other settings files upon.
"""

import environ
from django.conf import settings
from django.contrib.messages import constants as messages
from django.utils.translation import ugettext_lazy as _

ROOT_DIR = (
    environ.Path(__file__) - 3
)  # (proejctbat-beta1.0/config/settings/base.py - 3 = proejctbat-beta1.0/)
APPS_DIR = ROOT_DIR.path("bat")

env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR.path(".env")))

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
LANGUAGE_CODE = "en"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [ROOT_DIR.path("locale")]
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
    "django.contrib.humanize",  # Handy template tags
    # Model translation should be avove contrib.admin to work well.
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.postgres",
]
THIRD_PARTY_APPS = [
    # Rest Framwork
    "corsheaders",
    "rest_framework",
    # Django Filter
    "django_filters",
    # Django Swagger for documentation
    "rest_framework_swagger",
    # Crispy Forms
    "crispy_forms",
    # mptt for managing tree like strcuture for categories
    "mptt",
    # Sorl Thumbnail is used to create image Thumbnail
    "sorl.thumbnail",
    # Country list with flag and country code
    "django_countries",
    # roles
    "rolepermissions",
    # email
    "dbmail",
    "django_ses",
    # Model Histroy plugin
    "reversion",
    "reversion_compare",
    # countable fields
    "countable_field",
    # Currency and currency conversion
    "djmoney",
    # Django plans
    "plans",
    "ordered_model",
    # Django Defender
    "defender",
    # Django Invitation
    "invitations",
    # Django Notifications
    "notifications",
    # MultiSelectField
    "multiselectfield",
    # Tags
    "taggit",
    # Django selectable
    "selectable",
]

LOCAL_APPS = [
    "bat.users.apps.UsersConfig",
    "bat.core.apps.CoreConfig",
    "bat.setting.apps.SettingConfig",
    "bat.company.apps.CompanyConfig",
    "bat.product.apps.ProductConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# Django country Setting django_countries
COUNTRIES_FIRST = [
    "US",
    "GB",
    "SE",
    "CA",
    "CN",
    "DK",
    "FI",
    "FR",
    "DE",
    "IT",
    "JP",
    "NL",
    "NO",
    "ES",
]
# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules


# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
# change from django.contrib.auth.backends.ModelBackend to bat.users.backends.EmailOrUsernameModelBackend
AUTHENTICATION_BACKENDS = ["bat.users.backends.EmailOrUsernameModelBackend"]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "core:dashboard"


# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
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
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
STATIC_ROOT = str(ROOT_DIR("staticfiles"))
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR.path("static"))]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR("project_content"))
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/project_content/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR.path("templates"))],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                # Context processors use to make data available for global use
                "bat.globalprop.processors.processors.vendor_categories",
                "bat.globalprop.processors.processors.saleschannels",
                "bat.globalprop.processors.processors.loggedin_member",
                # Inbuild context from Django
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "plans.context_processors.account_status",
            ],
        },
    }
]
# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)

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
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/2.2/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("batadmin", "chetan@volutz.com")]
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


# django-compressor
# ------------------------------------------------------------------------------
# https://django-compressor.readthedocs.io/en/latest/quickstart/#installation
INSTALLED_APPS += ["compressor"]
STATICFILES_FINDERS += ["compressor.finders.CompressorFinder"]
# Your stuff...
# ------------------------------------------------------------------------------

MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}


# roles
ROLEPERMISSIONS_MODULE = "config.roles"
# Filehandle
FILE_UPLOAD_HANDLERS = (
    "django_excel.ExcelMemoryFileUploadHandler",
    "django_excel.TemporaryExcelFileUploadHandler",
)


# Add reversion models to admin interface:
ADD_REVERSION_ADMIN = True
# AMAZON PPC
AMAZON_PPC_AUTH_ENDPOINT = env(
    "AMAZON_PPC_AUTH_ENDPOINT", default="https://www.amazon.com/ap/oa"
)
AMAZON_PPC_TOKEN_ENDPOINT = env(
    "AMAZON_PPC_TOKEN_ENDPOINT", default="https://api.amazon.com/auth/o2/token"
)
AMAZON_PPC_AUTH_SCOPE = env(
    "AMAZON_PPC_AUTH_SCOPE", default="cpc_advertising:campaign_management"
)
AMAZON_PPC_CLIENT_ID = env("AMAZON_PPC_CLIENT_ID")
AMAZON_PPC_CLIENT_SECRET = env("AMAZON_PPC_CLIENT_SECRET")
AMAZON_PPC_PROFILE_ID = env(
    "AMAZON_PPC_PROFILE_ID", default="2719691478200925"
)
AMAZON_PPC_REGION = env(
    "AMAZON_PPC_REGION", default="advertising-api-test.amazon.com"
)

# Keyword rank page limit
KEYWORD_RANK_PAGE_LIMIT = env("KEYWORD_RANK_PAGE_LIMIT")

# enable REDIS_HOST if we are using same machine as Django
REDIS_URL = env("REDIS_URL")

# Django Plan Attributes
PLANS_CURRENCY = "USD"
DEFAULT_FROM_EMAIL = "chetan@volutz.com"
PLANS_INVOICE_ISSUER = {
    "issuer_name": "Bonum Mane AB",
    "issuer_street": "Libro ringväg 51",
    "issuer_zipcode": "752 28",
    "issuer_city": "Uppsala",
    "issuer_country": "SE",  # Must be a country code with 2 characters
    "issuer_tax_number": "SE559009135001",
}
PLANS_TAXATION_POLICY = "plans.taxation.eu.EUTaxationPolicy"
PLANS_TAX_COUNTRY = "SE"

# django-defender
DEFENDER_LOGIN_FAILURE_LIMIT = 3
DEFENDER_DISABLE_IP_LOCKOUT = True
DEFENDER_LOCKOUT_TEMPLATE = "user/lockout.html"

# Dajngo Invitation
INVITATIONS_SIGNUP_REDIRECT = "accounts:signup"
INVITATIONS_GONE_ON_ACCEPT_ERROR = False
INVITATIONS_INVITATION_MODEL = "users.InvitationDetail"

# Django Notifications
DJANGO_NOTIFICATIONS_CONFIG = {"USE_JSONFIELD": True}

# Django Taggit
TAGGIT_CASE_INSENSITIVE = True

# Some Global Variable for app
STATUS_PRODUCT = env.bool("STATUS_PRODUCT", "Product")

# Whitelist URL that frontend can be server on
CORS_ORIGIN_WHITELIST = env.list(
    "DJANGO_ALLOWED_HOSTS", default=["beta.thebatonline.com"]
)

# Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}
