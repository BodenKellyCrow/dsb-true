# doomscrollr/wsgi.py

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doomscrollr.settings')

application = get_wsgi_application()
# Django wsgi.py placeholder
