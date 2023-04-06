"""
Django settings for frontend project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# Read SECRET_KEY from env var, or gen new key if not present
SECRET_KEY = os.environ.get('SECRET_KEY')
if SECRET_KEY is None:
    SECRET_KEY = get_random_secret_key()

# Read ALLOWED_HOSTS from env var, or use wildcard if not present
try:
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')
except AttributeError:
    ALLOWED_HOSTS = ['*']

# Add all allowed hosts to CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = []
for i in ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS.append(f'http://{i}')
    CSRF_TRUSTED_ORIGINS.append(f'https://{i}')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Application definition

INSTALLED_APPS = [
    'node_configuration.apps.NodeConfigurationConfig',
    'api.apps.ApiConfig',
    'webapp.apps.WebappConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pwa',
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

ROOT_URLCONF = 'frontend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'frontend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join('.', 'node_modules', 'bootstrap', 'dist', 'css'),
    os.path.join('.', 'node_modules', 'bootstrap', 'dist', 'js'),
    os.path.join('.', 'node_modules', 'bootstrap-icons', 'font'),
    os.path.join('.', 'node_modules', 'spinkit'),
    os.path.join('.', 'node_modules', 'jquery', 'dist'),
    os.path.join('.', 'node_modules', 'smoothscroll-polyfill', 'dist'),
    os.path.join('.', 'node_modules', 'rangeslider.js', 'dist'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# PWA Config (django-pwa)
PWA_APP_NAME = 'Micropython Smarthome'
PWA_APP_DESCRIPTION = "Frontend for controlling, creating, and configuring micropython smarthome nodes."
#PWA_APP_THEME_COLOR = '#ffffff'
#PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/api'
#PWA_APP_STATUS_BAR_COLOR = 'black-translucent'
PWA_APP_ICONS = [
    {
        'src': '/static/webapp/android/android-launchericon-192-192.png',
        'sizes': '192x192'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/webapp/ios/256.png',
        'sizes': '256x256'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/webapp/ios/256.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

# Custom service worker
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'webapp', 'serviceworker.js')
