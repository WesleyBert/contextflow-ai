from celery import Celery

from src.infrastructure.config import get_settings

settings = get_settings()

celery_app = Celery(
    "contextflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.infrastructure.queue.tasks"],
)

celery_app.conf.task_track_started = True
