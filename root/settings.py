import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure--2xp^$&f6^pq77e^sp#r2e3%jw5^2#zzw#kki__ei%0pqo7&$)'

load_dotenv('.env')

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'jazzmin',
    'channels',
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.apps.AppsConfig',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'root.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'root.wsgi.application'
AUTH_USER_MODEL = 'apps.User'
ASGI_APPLICATION = "root.asgi.application"
DATABASES = {
    "default": {
        "ENGINE": os.getenv('DB_ENGINE'),
        "NAME": os.getenv('DB_NAME'),
        "USER": os.getenv('DB_USER'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": os.getenv('DB_HOST'),
        "PORT": os.getenv('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PAYMENT = {
    'CLICK': {
        'CLICK_MERCHANT_ID': os.getenv('CLICK_MERCHANT_ID'),
        'CLICK_MERCHANT_USER_ID': os.getenv('CLICK_MERCHANT_USER_ID'),
        'CLICK_SERVICE_ID': os.getenv('CLICK_SERVICE_ID'),
        'CLICK_SECRET_KEY': os.getenv('CLICK_SECRET_KEY'),
        'CLICK_API': os.getenv('CLICK_API')
    },
    'PAYME': {
        'PAYME_ID': os.getenv('PAYME_ID'),
        'PAYME_KEY': os.getenv('PAYME_KEY'),
        'PAYME_ACCOUNT': os.getenv('PAYME_ACCOUNT'),
        'PAYME_CALL_BACK_URL': os.getenv('PAYME_CALL_BACK_URL'),
        'PAYME_URL': os.getenv('PAYME_URL')
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv("HOST"), 6379)],
        },
    },
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
from root.rest_settings import *  # noqa
from root.ckeditor_settings import *
from root.jazzmin_settings import *
