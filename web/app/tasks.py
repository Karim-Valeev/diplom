import time

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger('celery.task.server')


@shared_task
def check_celery(msg):
    time.sleep(5)
    logger.info('Received message: %r', msg)
    return True
