from .settings import *

# Test settings
SECRET_KEY = 'django-insecure-test-key-123'
DEBUG = False

# Use in-memory SQLite database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use simple cache backend
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable CSRF protection in tests
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if middleware != 'django.middleware.csrf.CsrfViewMiddleware'
]

# Use Redis mock for testing
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}