#!/usr/bin/env python
# ==============================================================================
# FILE: backend/manage.py
# PURPOSE: Command-line entry point for administrative tasks, migrations, and development server.
# VIVA EXPLANATION: Standard Django CLI controller executing management commands (e.g., runserver, migrate, createsuperuser) pointing to config.settings.
# ==============================================================================

import os
import sys


# --- main ---
# What it does: Sets default settings module and executes administrative CLI commands via Django management engine.
# Why it's structured this way: Standard entry point for all command line interactions with the backend service.
# Parameters & Returns: CLI arguments passed via sys.argv.
# ------------------------------------------------------------------------------
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django is not installed. Run: pip install -r requirements.txt") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

