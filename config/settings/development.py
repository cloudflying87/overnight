"""
Development settings for OvernightApp project.

This module is also used for the self-hosted deployment (see
DJANGO_SETTINGS_MODULE in .env), because the full production.py profile
requires Cloudflare R2 settings that this deployment doesn't use. To get
production-like behaviour there (friendly error pages + admin error emails),
set DEBUG=False in the environment: DEBUG is read from the environment below
rather than hard-coded, and the debug-only conveniences are gated on it.
"""

from .base import *

# DEBUG is environment-driven so the deployed instance can run with DEBUG=False
# (which enables the friendly 500/404 pages and admin error emails) while local
# development defaults to DEBUG=True.
DEBUG = env.bool('DEBUG', default=True)

# ALLOWED_HOSTS comes from base.py (reads from .env or environment variable)
# Don't override it here!

# Use WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if DEBUG:
    # --- Local development conveniences (only when DEBUG is on) ---

    # Debug toolbar
    INSTALLED_APPS += [
        'debug_toolbar',
    ]
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INTERNAL_IPS = [
        '127.0.0.1',
    ]

    # Email backend - console output for development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    # Disable HTTPS redirect in development
    SECURE_SSL_REDIRECT = False

    # Allow weaker passwords in development (for testing)
    AUTH_PASSWORD_VALIDATORS = []

    # Faster fail on DB connect during local development
    DATABASES['default']['OPTIONS']['connect_timeout'] = 5
else:
    # --- Deployed instance (DEBUG=False) ---
    # EMAIL_BACKEND / EMAIL_* come from base.py, which reads them from the
    # environment (Brevo SMTP is configured in .env). Combined with the
    # mail_admins logging handler + ADMINS in base.py, unhandled 500 errors are
    # emailed to the admins. The require_debug_false filter on that handler only
    # passes when DEBUG is False, which is why error emails require this branch.
    SECURE_SSL_REDIRECT = False  # TLS is terminated by the upstream reverse proxy
