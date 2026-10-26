# ==============================================================================
# FILE: backend/config/asgi.py
# PURPOSE: Asynchronous Server Gateway Interface (ASGI) entry-point for async protocols.
# VIVA EXPLANATION: Serves as the ASGI callable for ASGI-compatible servers (such as Uvicorn or Daphne) enabling asynchronous request handling and WebSockets.
# ==============================================================================

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()

