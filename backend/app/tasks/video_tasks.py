from app.services.pipeline import process_video_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.video_tasks.process_video_task", bind=True)
def process_video_task(self, job_id: str, video_id: str) -> None:
    process_video_job(job_id=job_id, video_id=video_id)

