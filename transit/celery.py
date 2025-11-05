# transit/celery.py

import os
from celery import Celery

# Définir le module de configuration de Django pour le programme Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transit.settings')

# Créer une instance de l'application Celery
# Le nom peut être ce que vous voulez.
app = Celery('transit')

# Charger la configuration à partir du fichier settings.py de Django
# (CELERY_BROKER_URL, etc.)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les fichiers tasks.py de toutes les applications
app.autodiscover_tasks()

