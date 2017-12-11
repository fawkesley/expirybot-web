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
