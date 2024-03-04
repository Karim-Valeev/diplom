from celery import shared_task
from celery.utils.log import get_task_logger

from app.models import Video

logger = get_task_logger('celery.task.server')


@shared_task
def recognize_actions(video_id: int):
    video = Video.objects.filter(id=video_id).first()
    if video:
        logger.info('Video:  %r', video.title)
        # TODO: Сделай хотя бы пока тупую логику влоб,
        #  потом это в классы и методы логики обернешь
        raise NotImplementedError

    else:
        logger.info('There is no such video with id: %r', video_id)
    return True
