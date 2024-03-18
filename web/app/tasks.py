import subprocess
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from celery.utils.log import get_task_logger
from django.conf import settings
from server.celery import app

from app.models import Recognition, Video

logger = get_task_logger('celery.task.server')


# TODO: 1. Подумать над тем,
#  чтобы добавить селери задаче своих кастомных статусов,
#  тк появляются различные этапы всего действия,
#  которые могут интересны пользователю или показательны
#  для Дипломной системы

# TODO: 2. По сути это надо переделать в pandas DataFrame

# TODO: 3. Отсортировать колонны по последнему элементу по убыванию


def _draw_pie_chart(action_counters: dict, pie_chart_path: Path):
    sorted_action_counters = {
        k: v for k, v in sorted(
            action_counters.items(),
            key=lambda x: x[1],
            reverse=True
        )
    }
    counters = np.array(list(sorted_action_counters.values()))

    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.suptitle('Соотношение количества действий', fontsize=16)
    ax1.remove()
    ax2.pie(counters, startangle=90, autopct='%1.2f%%', radius=1.5)
    sum = counters.sum()
    labels = [
        '{0} - {1:1.2f} %'.format(
            k, (v / sum) * 100
        ) for k, v in sorted_action_counters.items()
    ]
    ax2.legend(
        title='Actions:',
        loc='center left',
        labels=labels,
        bbox_to_anchor=(-1.375, 0.5)
    )
    plt.savefig(pie_chart_path, dpi=300)
    plt.clf()  # Clearing plot.


def _convert_frame_to_time(frame: int, time_measure_unit: str, fps: int):
    res = 0
    if time_measure_unit == 'fr':
        res = frame
    elif time_measure_unit == 's':
        res = frame / fps
    elif time_measure_unit == 'm':
        res = frame / fps / 60
    elif time_measure_unit == 'h':
        res = frame / fps / 60 / 60
    return round(res, 1)


def _choose_ticks_measure_unit(frames_amount: int, fps: int) -> str:
    """Choosing X plot ticks time measure unit."""
    time_measure_unit = ''
    if frames_amount / fps <= 1:
        time_measure_unit = 'fr'
    else:
        if frames_amount / fps / 60 <= 1:
            time_measure_unit = 's'
        else:
            if frames_amount / fps / 60 / 60 <= 1:
                time_measure_unit = 'm'
            else:
                time_measure_unit = 'h'
    return time_measure_unit


def _draw_graph(frames_arr, action_counters, fps, graph_path):
    frames_amount = frames_arr.shape[0]
    frames_arr[frames_arr >= 0.2] = 1  # Threshold check.
    frames_arr = np.cumsum(frames_arr, axis=0)  # Сumulating action frames.

    x_frames = np.arange(start=1, stop=frames_amount + 1)  # X axis indices.
    fig, ax = plt.subplots(1)
    fig.suptitle('График кол-ва действий в течение времени', fontsize=16)
    ax.set_xlim(left=0, right=frames_amount)
    ax.set_ylim(bottom=0, top=frames_amount)
    for i, key in enumerate(action_counters):
        ax.plot(x_frames, frames_arr[:, i], label=key)
    time_measure_unit = _choose_ticks_measure_unit(frames_amount, fps)
    ticks, _ = plt.xticks()
    ticks = ticks[ticks <= frames_amount]  # Fixing last outside tick.
    labels = [
        '%g %s' % (
            _convert_frame_to_time(fr, time_measure_unit, fps),
            time_measure_unit,
        ) for fr in ticks
    ]
    plt.xticks(ticks, labels)
    plt.xlabel('Продолжительность видео')
    plt.ylabel('Количество действий в кадре')
    ax.legend()
    plt.savefig(graph_path, dpi=300)
    plt.clf()  # Clearing plot.


# TODO: 4. Подумать над ситуацией,
#  когда в кадре несколько действий одного типа!!!
# TODO: 5. Выводить логи на важных этапах задачи

def _draw_statistics(
        output_file_path: str, fps: int, pie_chart_path: Path, graph_path: Path
):
    with (open(output_file_path, 'r') as file):
        text = file.read()
        start = text.find('FPS:')
        end = text.find('Stream closed.')
        if start == -1 or end == -1:
            logger.error('Wrong output file structure.')
            return None, None
        text = '\n' + text[start:end]
        frames = text.split('\nFPS:')
        frames_amount = len(frames)

        # 2D np array with 5 columns for action classes probabilities.
        frames_arr = np.zeros((frames_amount, 5))
        action_counters = {
            'at the blackboard': 0,
            'making notes': 0,
            'talking': 0,
            'using computer': 0,
            'using phone': 0,
        }
        for i, frame in enumerate(frames):
            # Example: making notes: 27%
            for j, key in enumerate(action_counters):
                key_pos = frame.find(key)
                if key_pos != -1:
                    percent_start = key_pos + len(key + ': ')
                    percent_end = frame.find('%', key_pos, key_pos + 25)
                    percent = int(frame[percent_start:percent_end]) / 100
                    frames_arr[i][j] = percent
                    action_counters[key] += 1

        _draw_pie_chart(action_counters, pie_chart_path)
        _draw_graph(frames_arr, action_counters, fps, graph_path)


def _prep_rec_filepath(path: str) -> str:
    return path.strip(f'{settings.MEDIA_ROOT}/')


@app.task(bind=True)
def recognize_actions(self, video_id: int):
    video: Video = Video.objects.filter(id=video_id).first()
    if video:
        data = settings.YOLO_DATA_FILE
        cfg = settings.YOLO_CONFIG_FILE
        weights = settings.YOLO_WEIGHTS_FILE
        video_path = video.file.path
        filename = video_path.split('/')[-1]
        filename_without_ext = filename.strip('.mp4')

        # TODO: Вынести или укоротить
        result_video_dir = Path(
            f'{settings.MEDIA_ROOT}/users/{video.user_id}/recognitions/'
        )
        output_file_dir = Path(
            f'{settings.MEDIA_ROOT}/users/{video.user_id}/outputs/'
        )
        pie_chart_dir = Path(
            f'{settings.MEDIA_ROOT}/users/{video.user_id}/stats/pie_charts/'
        )
        graph_dir = Path(
            f'{settings.MEDIA_ROOT}/users/{video.user_id}/stats/graphs/'
        )

        result_video_dir.mkdir(parents=True, exist_ok=True)
        output_file_dir.mkdir(parents=True, exist_ok=True)
        pie_chart_dir.mkdir(parents=True, exist_ok=True)
        graph_dir.mkdir(parents=True, exist_ok=True)

        result_video_path = str(
            result_video_dir / f'recognized_{filename}'
        )
        output_file_path = str(
            output_file_dir / f'recognized_{filename_without_ext}.txt'
        )

        logger.info('Executing darknet command...')
        code = subprocess.call(
            f'darknet detector demo {data} {cfg} {weights} '
            f'-dont_show {video_path} -out_filename {result_video_path} '
            f'> {output_file_path}',
            shell=True
        )
        # TODO: 6. Какая-то проблема с сохраняемым форматом MPEG-4
        logger.info('Command returned code: %r', code)

        # Creating statistics plots:
        cam = cv2.VideoCapture(result_video_path)
        fps = round(cam.get(cv2.CAP_PROP_FPS))  # Get video frame rate.

        pie_chart_path = (
            pie_chart_dir / f'recognized_{filename_without_ext}_pie_chart.jpg'
        )
        graph_path = graph_dir / f'recognized_{filename_without_ext}_graph.jpg'
        _draw_statistics(output_file_path, fps, pie_chart_path, graph_path)

        task_id = self.request.id
        rec = Recognition.objects.filter(
            video_id=video_id, task_id=task_id
        ).first()
        if rec:
            rec.recognized_file = _prep_rec_filepath(result_video_path)
            rec.output_file = _prep_rec_filepath(output_file_path)
            rec.stat_pie_chart = _prep_rec_filepath(str(pie_chart_path))
            rec.stat_graph = _prep_rec_filepath(str(graph_path))
            rec.save()
            logger.info(
                'Recognized video and statistics saved and stored in DB.'
            )
        else:
            logger.warning(
                'There is no such recognition for video[%r] and task[%r].',
                video_id,
                task_id,
            )
    else:
        logger.warning('There is no such video with id: %r', video_id)
    return True
