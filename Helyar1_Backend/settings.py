from pathlib import Path

import os
import environ


env = environ.Env(
    DEBUG=(bool, False)  # default False if not set
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    #'jazzmin',  # For Admin UI Customization
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    
    #Local Apps
    'accounts.apps.AccountsConfig',
    'offers.apps.OffersConfig',
    'user_profile.apps.UserProfileConfig',
    'notifications.apps.NotificationsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'logo.apps.LogoConfig',
    
    #Third-Party Apps
    'django_cleanup.apps.CleanupConfig', # For cleaning up old files
    'rest_framework',
    'rest_framework_simplejwt', # For JWT Authentication# For Automated documentation
    'rest_framework_simplejwt.token_blacklist', # For Blacklisting Refresh Tokens
    'drf_spectacular', # For Automated documentation OpenAPI 3.0
    'drf_spectacular_sidecar', # To support spectacular when it will be deployed on production
    'django_celery_beat', # For celery
    
]


AUTH_USER_MODEL='accounts.User'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Helyar1_Backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'logo.context_processors.site_settings', # came from context processors.py files site_settings function to change admin panel logo
            ],
        },
    },
]

WSGI_APPLICATION = 'Helyar1_Backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]



# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'


#MEDIA FILES (User Uploaded Content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Helyar1 Project API Documentation',
    'DESCRIPTION': 'drf-spectacular generated API documentation for Helyar1 Project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'TAGS': [
        {'name': 'accounts'},
        
    ],
}




# Logging configuration for debuging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Keep default Django loggers
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module}:{lineno} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',  # Minimum level that will be printed
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'project.log'),
            'formatter': 'verbose',
        },
    },
    'root': {  # <-- All loggers will inherit this by default
        'handlers': ['console', 'file'],
        'level': 'DEBUG',  # Logs DEBUG, INFO, WARNING, ERROR, CRITICAL
    },
}


# JAZZMIN_UI_TWEAKS = {
#     "theme": "darkly",
# }

# JAZZMIN_SETTINGS = {
#     "site_title": "Maximum Savings",
#     "site_header": "Maximum Savings Admin",
#     "welcome_sign": "Welcome to Maximum Savings",
    
#     "site_logo": "logos/admin(1).png",  # Must exist in STATICFILES_DIRS
#     "site_logo_classes": "img-circle",
#     "site_icon": None,
# }

# Mail Configuration

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

#Phone Number Validation API Key
PHONE_NUMBER_VALIDATION_API_KEY = env("PHONE_NUMBER_VALIDATION_API_KEY")


from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Example: 5 minutes
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # Example: 1 day
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': 'your_secret_key',  # Replace with a strong, secret key (ideally from environment variables)
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(days=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=30),
}


# Stripe Configuration
STRIPE_API_KEY=env("STRIPE_API_KEY")
STRIPE_PUBLISHABLE_KEY=env("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET=env("STRIPE_WEBHOOK_SECRET")



DOMAIN = 'http://localhost:3000'  # MY React app URL

# Plan prices in cents
STRIPE_PRICES = {
    'basic': 599,    # $5.99
    'premium': 999,  # $9.99
}




#Netcore api setup
NETCORE_CE_API_KEY = env('NETCORE_CE_API_KEY')
NETCORE_EMAIL_API_KEY = env('NETCORE_EMAIL_API_KEY')
FROM_EMAIL = env('FROM_EMAIL')

# Twilio setup (Fixed: TWILLIO -> TWILIO)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER')

# Celery Configuration (Fixed: Use env.list for CELERY_ACCEPT_CONTENT)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = env.list('CELERY_ACCEPT_CONTENT', default=['json'])
CELERY_TASK_SERIALIZER = env('CELERY_TASK_SERIALIZER', default='json')
CELERY_RESULT_SERIALIZER = env('CELERY_RESULT_SERIALIZER', default='json')
CELERY_TIMEZONE = env('CELERY_TIMEZONE', default='UTC')

# Optional: For scheduled tasks (if using Celery Beat)
CELERY_BEAT_SCHEDULER = env('CELERY_BEAT_SCHEDULER', default='django_celery_beat.schedulers:DatabaseScheduler')

#GOOGLE LOGIN SETUP

GOOGLE_CLIENT_ID=env('GOOGLE_CLIENT_ID')
GOOELE_CLIENT_SECRET=env('GOOGLE_CLIENT_SECRET')