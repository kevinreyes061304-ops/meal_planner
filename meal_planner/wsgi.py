"""
WSGI config for meal_planner project - Vercel Version with Auto-Setup
"""

import os
import sys
from pathlib import Path

# Add the project directory to the sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_planner.settings')

# Import Django's WSGI application
from django.core.wsgi import get_wsgi_application

# Initialize Django
application = get_wsgi_application()

# Auto-run migrations and create admin user on cold start
def setup_database():
    """Run migrations and create default admin user if needed"""
    try:
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        from django.db import connection
        
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user';"
            )
            tables = cursor.fetchall()
        
        # If auth_user table doesn't exist, run migrations
        if not tables:
            print("Running migrations...")
            call_command('migrate', '--noinput', verbosity=0)
            print("Migrations completed!")
            
            # Create default admin user
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                print("Default admin user created (username: admin, password: admin123)")
        
    except Exception as e:
        print(f"Database setup error (non-critical): {e}")
        pass

# Run setup on module load
setup_database()

# Vercel expects 'app' variable
app = application