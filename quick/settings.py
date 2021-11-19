# Django settings for QUICK project.
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')
import django

# This is the list of http server request names the site is allowed to serve for

ALLOWED_HOSTS = ['*']

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Force Django to use the systems timezone
TIME_ZONE =  'Asia/Shanghai'

# Language section
# TBD.
LANGUAGE_CODE = 'zh-cn'
USE_I18N = False
DEFAULT_CHARSET = 'utf-8'
SITE_ID = 1
# Logger
BASE_LOG_DIR = "/var/log/quick/"
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s\t%(pathname)s\t[%(module)s:%(lineno)d]\t%(levelname)s\t%(message)s',
        },
        'simple': {
            'format': '%(levelname)s\t%(asctime)s\t[%(filename)s:%(lineno)d]\t%(message)s'
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, "info.log"),
            'maxBytes': 1024 * 1024 * 500,
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'auth': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, "auth.log"),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, "django.log"),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, "err.log"),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default','error'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['django'],
            'level': 'INFO',
            'propagate': True,
        },
        'auth': {
            'handlers': ['auth'],
            'level': 'INFO',
        }
    },
}
# not used
MEDIA_ROOT = '/var/www/quick_content/temp/'
MEDIA_URL = '/media/'

if django.VERSION[0] == 1 and django.VERSION[1] < 4:
    ADMIN_MEDIA_PREFIX = '/media/'
else:
    STATIC_URL = '/media/'

SECRET_KEY = 'K/YO3Psl+ulFWz1A+nJdoTe8ihso0DaBIb59Uxn36RBpEtKSx8WVYg=='
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'yourmail@163.com'
EMAIL_HOST_PASSWORD = 'yourmailpassword'
# code config

if django.VERSION[0] == 1 and django.VERSION[1] < 4:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.load_template_source',
        'django.template.loaders.app_directories.load_template_source',
    )
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

if django.VERSION[0] == 1 and django.VERSION[1] < 2:
    # Legacy django had a different CSRF method, which also had
    # different middleware. We check the vesion here so we bring in
    # the correct one.
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.csrf.middleware.CsrfMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    )

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    '/usr/share/quick/quick/templates',
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'quick',
)
# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quick',
        'USER':'root',
        'PASSWORD': 'root',
        'HOST':'localhost',
        'PORT':'3306',
    }
}

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
)

#SESSION_ENGINE = 'django.contrib.sessions.backends.file'
#SESSION_FILE_PATH = '/usr/share/quick/sessions'
SESSION_ENGINE = "django.contrib.sessions.backends.db"

