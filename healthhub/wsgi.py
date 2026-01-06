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

# Add your project directory to the sys.path
project_home = '/home/araj1/HealthHub-Where-Fitness-Meets-Wellness'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable to tell Django where your settings are
os.environ['DJANGO_SETTINGS_MODULE'] = 'healthhub.settings'

# Activate your virtual environment
activate_this = '/home/araj1/HealthHub-Where-Fitness-Meets-Wellness/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()