import os
import django
from django.conf import settings

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'microfinance.settings')
django.setup()

# Print paths
print(os.path.join(settings.STATIC_ROOT, 'css', 'mf.css'))
print(os.path.join(settings.STATIC_ROOT, 'css', 'pdf_stylesheet.css'))
