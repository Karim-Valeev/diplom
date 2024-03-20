from enum import Enum

from celery.result import AsyncResult
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404

from app.models import Recognition, Video
from app.tasks import recognize_actions


class RecognitionStatuses(Enum):
    """
    Depending on the name of the status, it returns its translation and a flag
    for the possibility of starting the next recognition.
    """
    PENDING = 'Задача в ожидании запуска или утеряна, можете попробовать еще раз.', True
    STARTED = 'Задача запустилась.', False
    RECOGNIZING = 'Идет распознавание...', False
    SUCCESS = 'Завершилось!', True
    FAILURE = 'Возникла ошибка. Свяжитесь с администратором.', False


def start_recognition(video_id: int):
    async_res = recognize_actions.delay(video_id)
    Recognition.objects.create(video_id=video_id, task_id=async_res.task_id)


def get_recognition_task_status(video: Video) -> tuple[str | None, bool]:
    recognition = video.recognitions.order_by('created').last()
    if recognition:
        task_id = recognition.task_id
        if task_id:
            async_res = AsyncResult(task_id)
            return RecognitionStatuses[async_res.status].value
    return None, True


def get_recognized_video_response(recognition_id: int):
    recognition = get_object_or_404(Recognition, id=recognition_id)
    recognized_file = recognition.recognized_file
    path = recognized_file.path
    name = recognized_file.name.split('/')[-1]
    with open(path, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/force-download'
        )
        response['Content-Disposition'] = f'attachment; filename="{name}"'
        return response


def get_recognition_stats_response(recognition_id: int, stat_type: str | None):
    recognition = get_object_or_404(Recognition, id=recognition_id)
    if stat_type == 'graph':
        stat_file = recognition.stat_graph
    elif stat_type == 'pie_chart':
        stat_file = recognition.stat_pie_chart
    else:
        return HttpResponseBadRequest
    path = stat_file.path
    name = stat_file.name.split('/')[-1]
    with open(path, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/force-download'
        )
        response['Content-Disposition'] = f'attachment; filename="{name}"'
        return response
