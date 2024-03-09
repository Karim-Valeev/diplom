import os
import subprocess

from celery.utils.log import get_task_logger
from django.conf import settings

from app.models import Recognition, Video
from server.celery import app

logger = get_task_logger('celery.task.server')


@app.task(bind=True)
def recognize_actions(self, video_id: int):
    video: Video = Video.objects.filter(id=video_id).first()
    if video:
        data = settings.YOLO_DATA_FILE
        cfg = settings.YOLO_CONFIG_FILE
        weights = settings.YOLO_WEIGHTS_FILE

        video_path = video.file.path

        sep = os.sep
        file_parts = video_path.split(sep)
        file_root = sep.join(file_parts[:-1])
        filename = file_parts[-1]
        new_filename = f'recognized_{filename}'
        result_video_path = f'{file_root}{sep}{new_filename}'

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

        task_id = self.request.id
        recognition = Recognition.objects.filter(video_id=video_id, task_id=task_id).first()
        file_parts = result_video_path.split(
            f'{str(settings.MEDIA_ROOT)}{sep}'
        )
        recognized_file = file_parts[-1]
        recognition.recognized_file = recognized_file
        recognition.save()
        logger.info('Recognized video file saved and stored in DB.')

    else:
        logger.info('There is no such video with id: %r', video_id)
    return True
