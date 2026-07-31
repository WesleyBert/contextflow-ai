from celery import Celery

from src.infrastructure.config import get_settings
from src.infrastructure.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

celery_app = Celery(
    "contextflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.infrastructure.queue.tasks"],
)

celery_app.conf.task_track_started = True
# por padrão o Celery "sequestra" o root logger ao iniciar o worker (reconfigura os
# handlers do jeito dele) — desligado aqui pra não sobrescrever o handler JSON que
# `configure_logging()` acabou de montar.
celery_app.conf.worker_hijack_root_logger = False
