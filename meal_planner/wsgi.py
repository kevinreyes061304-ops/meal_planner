"""
WSGI config for meal_planner project - Vercel Version

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It exposes a module-level variable named
``application`` which is the WSGI application object.
"""

import os
import sys

# Add the project directory to the sys.path
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_planner.settings')

from django.core.management import execute_from_command_line
import sys

def create_admin():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

try:
    create_admin()
except:
    pass

application = get_wsgi_application()

# Vercel expects 'app' variable
app = application