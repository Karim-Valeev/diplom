from enum import Enum

from celery.result import AsyncResult
from django.http import FileResponse

from app.models import Recognition, Video
from app.tasks import recognize_actions


class RecognitionStatuses(Enum):
    """
    Depending on the name of the status, it returns its translation and a flag
    for the possibility of starting the next recognition.
    """
    PENDING = 'Задача прервалась, попробуйте еще раз.', True
    STARTED = 'В процессе...', False
    SUCCESS = 'Завершилось!', True
    FAILURE = 'Возникла ошибка.', False


def start_recognition(video_id: int):
    async_res = recognize_actions.delay(video_id)
    Recognition.objects.create(video_id=video_id, task_id=async_res.task_id)


def get_recognition_task_status(video: Video) -> tuple[str | None, bool]:
    # TODO: Try to optimize query with video join
    recognition = video.recognitions.order_by('created').last()
    if recognition:
        task_id = recognition.task_id
        if task_id:
            async_res = AsyncResult(task_id)
            return RecognitionStatuses[async_res.status].value
    return None, True


def get_recognized_video_response(recognition_id: int):
    recognition = Recognition.objects.filter(id=recognition_id).first()
    if recognition:
        recognized_file = recognition.recognized_file
        path = recognized_file.path
        name = recognized_file.name
        with open(path, 'rb') as file:
            response = FileResponse(
                file.read(),
                content_type='application/force-download'
            )
            response['Content-Disposition'] = f'attachment; filename="{name}"'
            return response
    else:
        # TODO: Raise 404 exception
        pass


def get_recognition_stats_response(recognition_id: int):
    recognition = Recognition.objects.filter(id=recognition_id).first()
    if recognition:
        raise NotImplementedError
    else:
        # TODO: Raise 404 exception
        pass
