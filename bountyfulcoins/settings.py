"""
Django settings for bountyfulcoins project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import os.path

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, 'bountyfulcoins/')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'PLEASE_GENERATE_A_NEW_KEY_FOR_PRODUCTION_PLEASE_THANK_YOU'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

ADMINS = (
    ('Bountyful Coins', 'contact@bountyfulcoins.com'),
)

ALLOWED_HOSTS = ['.bountyfulcoins.com']

# Set the Site ID
SITE_ID = 1

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'django_extensions',
    'south',
    'devserver',
    'registration',
    'captcha',
    'django_comments_xtd',

    'bountyfulcoinsapp',
)

COMMENTS_APP = "django_comments_xtd"

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bountyfulcoinsdb',
        'USER': 'bountyful',
        'PASSWORD': 'bountyful',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Devserver config
DEVSERVER_MODULES = (
    # 'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    # 'devserver.modules.ajax.AjaxDumpModule',
    # 'devserver.modules.profile.MemoryUseModule',
    # 'devserver.modules.cache.CacheSummaryModule',
    # 'devserver.modules.profile.LineProfilerModule',
)


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/site_media/'
STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, 'site_media'),)

# Template context processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "bountyfulcoins.context_processors.settings",
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(process)s - %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',

        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 20 * 1024 * 1024,
            'backupCount': 5,
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'bountyful.log'),
            'formatter': 'default',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'werkzeug': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'bountyfulcoinsapp': {
            'level': 'DEBUG',
            'propagate': True
        },
        '': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

# Internal bountyful app settings
ROOT_URLCONF = 'bountyfulcoins.urls'
WSGI_APPLICATION = 'bountyfulcoins.wsgi.application'
LOGIN_URL = '/login/'

TEST_RUNNER = 'django_coverage.coverage_runner.CoverageRunner'
COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', 'locale$', 'fixtures$'
    'common.views.test', '__init__', 'django',
    'migrations', 'south', 'registration', 'devserver', 'captcha'
]

ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window
RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = '6Ld6Su8SAAAAAEjAGF4Lt3mOzfhK6snc3Ub_SYBt'
RECAPTCHA_PRIVATE_KEY = 'PLEASE_USE_REAL_KEY_IN_PRODUCTION'

# an issue with pydns prevents this from working properly
CHECK_MX = False
CHECK_EMAIL_EXISTS = False

FEATURE_POST_MIN_CHARGE = 0.01594
FEATURE_POST_DAILY_CHARGE = 0.01594

ADDRESSES_LIVE_SYNC = True  # turn this off when running sync in cron
ADDRESSES_SYNC_FREQUENCE = 60 * 5  # five minutes

COMMENTS_XTD_MAX_THREAD_LEVEL = 8
