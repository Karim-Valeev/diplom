import subprocess
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger
from django.conf import settings
from server.celery import app

from app.models import Recognition, Video

logger = get_task_logger('celery.task.server')


DATA = settings.YOLO_DATA_FILE
CFG = settings.YOLO_CONFIG_FILE
WEIGHTS = settings.YOLO_WEIGHTS_FILE

ACTIONS = [
    'at the blackboard', 'making notes', 'talking', 'using computer', 'using phone'
]


def _call_darknet(video_path, buffer_file, output_file_path):
    """Recognizes actions in video file and generates txt outputs with frame info."""
    logger.info('Executing darknet command...')
    code = subprocess.call(
        f'darknet detector demo {DATA} {CFG} {WEIGHTS} '
        f'-dont_show {video_path} -out_filename {buffer_file} '
        f'> {output_file_path}',
        shell=True,
    )
    logger.info('darknet command returned code: %r', code)


def _call_ffmpeg(buffer_file, result_video_path):
    """Converts MPEG-4 codec video file to H.264."""
    logger.info('Executing ffmpeg conversion command...')
    code = subprocess.call(
        f'ffmpeg -i {buffer_file} -y -loglevel quiet -c:v libx264 -crf 23 '
        f'-preset medium {result_video_path}',
        shell=True,
    )
    logger.info('ffmpeg command returned code: %r', code)


def _draw_pie_chart(frames_df, pie_chart_path: Path):
    counters = frames_df.iloc[-1]

    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.suptitle('Соотношение количества действий', fontsize=16)
    ax1.remove()
    ax2.pie(counters, startangle=90, autopct='%1.2f%%', radius=1.5)
    sum = counters.sum()
    labels = [
        '{0} - {1:1.2f} %'.format(
            k, (v / sum) * 100
        ) for k, v in counters.items()
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


def _draw_graph(frames_df, fps, graph_path):
    frames_amount = frames_df.shape[0]
    x_frames = np.arange(start=1, stop=frames_amount + 1)  # X axis indices.
    fig, ax = plt.subplots(1)
    fig.suptitle('График кол-ва действий в течение времени', fontsize=16)
    ax.set_xlim(left=0, right=frames_amount)
    ax.set_ylim(bottom=0, top=frames_amount)
    for action in frames_df:
        ax.plot(x_frames, frames_df[action], label=action)
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


def _draw_statistics(
        output_file_path: str, fps: int, pie_chart_path: Path, graph_path: Path
) -> bool:
    logger.info('Creating statistics plots.')
    with (open(output_file_path, 'r') as file):
        text = file.read()
        start = text.find('FPS:')
        end = text.find('Stream closed.')
        if start == -1 or end == -1:
            logger.error('Wrong output file structure.')
            return False
        text = '\n' + text[start:end]
        frames = text.split('\nFPS:')

        # 2D np array with 5 columns for action classes probabilities.
        frames_arr = np.zeros((len(frames), len(ACTIONS)))
        frames_df = pd.DataFrame(data=frames_arr, columns=ACTIONS)
        for i, frame in enumerate(frames):
            for action in frames_df:
                action_pos = frame.find(action)
                if action_pos != -1:
                    percent_start = action_pos + len(action + ': ')
                    percent_end = frame.find('%', action_pos, action_pos + 25)
                    percent = int(frame[percent_start:percent_end]) / 100
                    frames_df.loc[i, action] = percent

        frames_df[frames_df >= 0.2] = 1  # Threshold check.
        frames_df = frames_df.cumsum()  # Cumulating action frames.
        # Sorting columns by their highest values.
        frames_df = frames_df.sort_values(by=[len(frames)-1], axis=1, ascending=False)

        _draw_graph(frames_df, fps, graph_path)
        _draw_pie_chart(frames_df, pie_chart_path)

        return True


def _prep_rec_filepath(path: str) -> str:
    return path.strip(f'{settings.MEDIA_ROOT}/')


@app.task(bind=True)
def recognize_actions(self, video_id: int):
    video = Video.objects.filter(id=video_id).first()
    if video:
        video_path = video.file.path
        filename = video_path.split('/')[-1]
        filename_without_ext = filename.strip('.mp4')

        base_dir = Path(f'{settings.MEDIA_ROOT}/users/{video.user_id}')
        result_video_dir = base_dir / 'recognitions'
        result_video_dir.mkdir(parents=True, exist_ok=True)
        output_file_dir = base_dir / 'outputs'
        output_file_dir.mkdir(parents=True, exist_ok=True)
        pie_chart_dir = base_dir / 'stats/pie_charts'
        pie_chart_dir.mkdir(parents=True, exist_ok=True)
        graph_dir = base_dir / 'stats/graphs'
        graph_dir.mkdir(parents=True, exist_ok=True)

        buffer_file = 'buffer.mp4'
        result_video_path = str(result_video_dir / f'recognized_{filename}')
        output_file_path = str(output_file_dir / f'recognized_{filename_without_ext}.txt')

        # TODO: Обдумать ситуацию, когда несколько действий в кадре

        # Recognize actions in video and generate txt output.
        self.update_state(state='RECOGNIZING')
        _call_darknet(video_path, buffer_file, output_file_path)
        _call_ffmpeg(buffer_file, result_video_path)

        cam = cv2.VideoCapture(result_video_path)
        fps = round(cam.get(cv2.CAP_PROP_FPS))  # Get video frame rate.

        # Creating statistics plots:
        pie_chart_path = (
            pie_chart_dir / f'recognized_{filename_without_ext}_pie_chart.jpg'
        )
        graph_path = graph_dir / f'recognized_{filename_without_ext}_graph.jpg'
        complete = _draw_statistics(output_file_path, fps, pie_chart_path, graph_path)

        task_id = self.request.id
        recognition = Recognition.objects.filter(
            video_id=video_id, task_id=task_id
        ).first()
        if recognition:
            recognition.recognized_file = _prep_rec_filepath(result_video_path)
            recognition.output_file = _prep_rec_filepath(output_file_path)
            msg = 'Recognized video %rsaved and stored in DB.'
            if complete:
                recognition.stat_pie_chart = _prep_rec_filepath(str(pie_chart_path))
                recognition.stat_graph = _prep_rec_filepath(str(graph_path))
                msg = msg % 'and statistics '
            recognition.save()
            logger.info(msg)
        else:
            logger.warning(
                'There is no such recognition for video[%r] and task[%r].',
                video_id, task_id,
            )
    else:
        logger.warning('There is no such video with id: %r', video_id)
    return True
