"""
Development settings for Travel Analytics project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database - Using SQLite for now (easy setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'travel_analytics_dev',  # ← TRAVEL ANALYTICS REFRESH DATABASE
        'USER': 'simoncrunden',      # Find with: whoami (bash)
        'PASSWORD': '',                   # Empty for local dev
        'HOST': 'localhost',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
    }
}

# CORS - Allow frontend in development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://localhost:3000',
]

CORS_ALLOW_CREDENTIALS = True
