from os import environ

from celery import Celery
from celery.signals import setup_logging

environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')


@setup_logging.connect  # override celery logger
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    from django.conf import settings
    dictConfig(settings.LOGGING)


app = Celery('server.settings')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(packages=['app'])

conf = app.conf
conf.timezone = 'UTC'

# Without this setting it is easy to reach limit of connection to Redis
conf.broker_pool_limit = int(environ.get('CELERY_BROKER_POOL_LIMIT', 0))
conf.broker_url = environ.get('CELERY_BROKER_URL', 'redis://localhost:6379')
conf.result_backend = environ.get(
    'CELERY_RESULT_BACKEND', 'redis://localhost:6379'
)
conf.result_expires = int(environ.get('CELERY_RESULT_EXPIRES', 300))
