# diplom
Это кодовая часть моей Выпускной Квалификационной Работы на тему
"Разработка инструментов идентификации действий обучающихся
на основе анализа видеопотока из аудиторий". Она содержит в себе
простую клиентскую часть, взаимодействующую с сервером Django,
который через фоновые задачи Celery вызывает
Модуль распознавания действий, использующий ML фреймворк DarkNet
с обученной моделью, для распознавания загруженных действий в загруженных видеофайлах.

### Требования:
* Операционная система Linux семейства Debian.
* Собранный CLI фреймворка DarkNet.
Ссылка на репозиторий: https://github.com/AlexeyAB/darknet.
* Установленный Python 3.10.
* Установленная CUDA 12.3 с совместимой видеокартой.
* Скачать актуальный файл с весами или создать свой:
[yolo.weights](https://drive.google.com/file/d/1_6XE5Xws1a1AsczcWSvAa4paYwWThS67/view?usp=sharing).
Переместить его в директорию ml/

### Настройка и запуск:
Docker:
`docker compose up -d -build`
Django:
```
python3.10 -m venv env
source env/bin/activate
cd web
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```
Celery:
`celery -A server worker -l INFO`
ML:
```
nvidia-smi  # Проверка того, что у CUDA есть свободное место для работы.
darknet detect cfg/yolo.data cfg/yolo.cfg yolo.weights test.jpg
darknet detector demo cfg/yolo.data cfg/yolo.cfg yolo.weights -ext_output test.mp4
darknet detector demo yolo.data yolo.cfg yolo.weights test.mp4 -out_filename res_test.mp4
```
