import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-+swhl(ar$w(2^)z8c9&f2!fb9hus&4&qa1=2lejm5haz!x5w*p'
DEBUG = bool(int(os.getenv('DEBUG', True)))

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

LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CONSTRUCTION_SUPPORT = os.getenv('CONSTRUCTION_SUPPORT_CONTACTS')
CUSTOMER_SUPPORT = os.getenv('CUSTOMER_SUPPORT_CONTACTS')

TIME_ZONE = "Europe/Moscow"
USE_TZ = False

INSTALLED_APPS = ("main",)


BOT_TOKEN = os.getenv('TELEGRAM_BOT_DEV_TOKEN', '')
if not DEBUG:
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
