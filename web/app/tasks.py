import os
import subprocess

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from app.models import Recognition, Video  # noqa

logger = get_task_logger('celery.task.server')


@shared_task
def recognize_actions(video_id: int):
    video: Video = Video.objects.filter(id=video_id).first()
    if video:
        logger.info('Video:  %r', video.title)
        data = settings.YOLO_DATA_FILE
        cfg = settings.YOLO_CONFIG_FILE
        weights = settings.YOLO_WEIGHTS_FILE
        video_path = video.file.path

        print(f'{video_path=}')
        file_parts = video_path.split(os.sep)
        print(f'{file_parts=}')
        file_root = '/'.join(file_parts[:-1])
        filename = file_parts[-1]
        new_filename = f'recognized_{filename}'

        result_video_path = f'{file_root}/{new_filename}'

        # TODO: Найти команду чтобы не открывалось еще одно окно
        # TODO: Похоже надо будет капчурить и парсить выхлоп команды
        # TODO: Обернуть в класс?

        code = subprocess.call(
            f'darknet detector demo '
            f'{data} {cfg} {weights} {video_path} '
            f'-out_filename {result_video_path}',
            shell=True
        )
        logger.info('Running terminal command returned code: %r', code)

        # with open(result_video_path) as f:
        #     print(f)
        #     Recognition.objects.create()

    else:
        logger.info('There is no such video with id: %r', video_id)
    return True
