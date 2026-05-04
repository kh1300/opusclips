from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "clipforge",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.tasks.video_tasks"],
)
celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    timezone="UTC",
)
