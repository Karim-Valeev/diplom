# DIPLOM PROJECT

### Настройка и запуск:

Celery:
`
celery -A server worker -l INFO
`

ML:
`
nvidia-smi  # Проверка того, что у CUDA есть место для работы
darknet detector train cfg/yolo.data cfg/yolo.cfg yolo.weights -clear
darknet detect cfg/yolo.data cfg/yolo.cfg yolo.weights test.jpg
darknet detector demo cfg/yolo.data cfg/yolo.cfg yolo.weights -ext_output test.mp4
darknet detector demo yolo.data yolo.cfg yolo.weights test.mp4 -out_filename res_test.mp4
`

### Особенности:
* Система совместима только с ОС Linux семейства Debian.
