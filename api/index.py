import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WellReserve.settings')


if os.environ.get('VERCEL'):
	django.setup()
	call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)

app = get_wsgi_application()