from typing import Any, Optional

from celery.app.log import TaskFormatter


class CeleryTaskFormatter(TaskFormatter):
    def __init__(self, *args: Any, datefmt: Optional[str] = None,
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.datefmt = datefmt
