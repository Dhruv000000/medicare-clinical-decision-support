# ==============================================================================
# FILE: backend/config/wsgi.py
# PURPOSE: Web Server Gateway Interface (WSGI) entry-point for synchronous HTTP deployment.
# VIVA EXPLANATION: Serves as the WSGI callable for production application servers (e.g., Gunicorn or uWSGI), forwarding incoming HTTP requests to Django.
# ==============================================================================

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

