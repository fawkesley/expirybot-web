from .common import *

import os

from django.core.exceptions import ImproperlyConfigured

import dj_database_url

try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    raise ImproperlyConfigured(
        "In production mode you must specify the `SECRET_KEY` environment "
        "variable. If you're _definitely not_ running in production it's safe "
        "to set this to something insecure, eg `export SECRET_KEY=foo`")
assert len(SECRET_KEY) > 20, "Bad (short) secret key: {}".format(SECRET_KEY)

DEBUG = False

ALLOWED_HOSTS = ['www.expirybot.com']

SERVE_STATIC_FILES = False

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES = {'default': db_from_env}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
