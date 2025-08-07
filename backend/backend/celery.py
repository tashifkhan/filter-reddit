import os

from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Load settings from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Broker connection settings
app.conf.broker_connection_retry_on_startup = False  # Don't retry connecting to broker on startup
app.conf.broker_connection_max_retries = 10  # Maximum number of retries if connection breaks

# Autodiscover tasks.py in installed apps
app.autodiscover_tasks()

# Dynamic queue configuration
queues = {
    "sub_reddit_fetch.tasks.run_sub_reddit_data.fetch_sub_reddit_data": {
        "queue": "sub_reddit_fetch"
    },
}

app.conf.task_routes = queues
