import subprocess

from celery.utils.log import get_task_logger
from django.conf import settings
from server.celery import app

from app.models import Recognition, Video

logger = get_task_logger('celery.task.server')


@app.task(bind=True)
def recognize_actions(self, video_id: int):
    video: Video = Video.objects.filter(id=video_id).first()
    if video:
        data = settings.YOLO_DATA_FILE
        cfg = settings.YOLO_CONFIG_FILE
        weights = settings.YOLO_WEIGHTS_FILE

        # TODO: Подумать над тем,
        #  чтобы добавить селери задаче своих кастомных статусов,
        #  тк появляются различные этапы всего действия,
        #  которые могут интересны пользователю или показательны
        #  для Дипломной системы

        video_path = video.file.path
        file_parts = video_path.split('/')
        filename = file_parts[-1]

        result_video_path = (
            f'{settings.MEDIA_ROOT}/users/'
            f'{video.user_id}/recognitions/recognized_{filename}'
        )
        output_file_path = (
            f'{settings.MEDIA_ROOT}/users/'
            f'{video.user_id}/outputs/recognized_{filename}_output.txt'
        )

        print(f'{result_video_path=}')

        code = subprocess.call(
            f'darknet detector demo '
            f'{data} {cfg} {weights} '
            f'-dont_show '
            f'{video_path} -out_filename {result_video_path} '
            f'> {output_file_path}',
            shell=True
        )
        # TODO: Возможно стоит вывод все равно
        #  тоже параллельно пускать в терминал

        # TODO: Не очень понятно на самом деле, че эти коды значат
        logger.info('Running terminal command returned code: %r', code)

        task_id = self.request.id
        recognition = Recognition.objects.filter(
            video_id=video_id, task_id=task_id).first()
        recognition.recognized_file = result_video_path.strip(
            f'{settings.MEDIA_ROOT}/'
        )
        recognition.save()
        logger.info('Recognized video file saved and stored in DB.')

    else:
        logger.info('There is no such video with id: %r', video_id)
    return True
