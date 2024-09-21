import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-+swhl(ar$w(2^)z8c9&f2!fb9hus&4&qa1=2lejm5haz!x5w*p'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'PORT': os.getenv('DATABASE_PORT'),
        'HOST': os.getenv('DATABASE_HOST'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = ("main",)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
