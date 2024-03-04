from django.http import FileResponse

from app.models import Recognition


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
