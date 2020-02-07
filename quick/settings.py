# Django settings for QUICK project.
import sys
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
TIME_ZONE = None

# Language section
# TBD.
LANGUAGE_CODE = 'en-us'
USE_I18N = False
DEFAULT_CHARSET = 'utf-8'
SITE_ID = 1

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
EMAIL_HOST_USER = 'yourname@163.com'
EMAIL_HOST_PASSWORD = 'yourpassword'
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

SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = '/usr/share/quick/sessions'
