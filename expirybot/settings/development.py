from .common import *
import os

# TOTALLY INSECURE: We only hard-code the SECRET_KEY in development
SECRET_KEY = 'insecure-development-key'

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'vagrant',
    }
}

SERVE_STATIC_FILES = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'debug.log'),
            'formatter': 'verbose',
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'info.log'),
            'formatter': 'verbose',
        },
        'warning_file': {
            'level': 'WARN',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'warning.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['debug_file', 'info_file', 'warning_file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

INSTALLED_APPS += [
    'debug_toolbar'
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
] + MIDDLEWARE


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda x: True,
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
