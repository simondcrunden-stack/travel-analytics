"""
Development settings for Travel Analytics project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database - Using SQLite for now (easy setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS - Allow frontend in development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://localhost:3000',
]

CORS_ALLOW_CREDENTIALS = True
