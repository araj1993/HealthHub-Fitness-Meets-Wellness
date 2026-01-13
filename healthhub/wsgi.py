"""
WSGI config for healthhub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthhub.settings')

# application = get_wsgi_application()

import os
import sys
from pathlib import Path

# Get the project directory dynamically
project_home = Path(__file__).resolve().parent.parent
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

# Set environment variable to tell Django where your settings are
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthhub.settings')

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()