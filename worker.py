from celery import Celery
import os
from dotenv import load_dotenv
import ssl
from celery.schedules import crontab

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "hr_agent",
    broker=REDIS_URL,
    backend=REDIS_URL
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE
    },
    redis_backend_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE
    },
)


celery_app.conf.beat_schedule = {
    "renew-gmail-watches-daily": {
        "task": "tasks.gmail_watch_renewal.renew_all_watches_task",
        "schedule": crontab(hour=3, minute=0),
    },
}

app = celery_app

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_email_task(self, email_id: str, user_id: str):
    """
    Main background task — runs full AI pipeline for one email.
    Called by Dev 1's service.py instead of calling tasks directly.
    """
    try:
        import asyncio
        from tasks.classifier import classify_and_save
        from tasks.duplicate import check_and_save
        from tasks.queue import check_needs_attention
        from rag.embedder import embed_and_save_email

        print(f"Processing email {email_id}...")

        classify_and_save(email_id)
        check_needs_attention(email_id, user_id)
        asyncio.run(check_and_save(email_id, user_id))
        asyncio.run(embed_and_save_email(email_id))

        print(f"Email {email_id} fully processed")
        return {"status": "success", "email_id": email_id}

    except Exception as exc:
        print(f"Error processing email {email_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_resume_task(self, email_id: str, user_id: str,
                        message_id: str, access_token: str):
    """
    Background task for resume processing.
    Separate from main pipeline since file download can be slow.
    """
    try:
        import asyncio
        from tasks.resume import process_resume_from_gmail

        asyncio.run(process_resume_from_gmail(
            access_token=access_token,
            message_id=message_id,
            email_id=email_id,
            user_id=user_id
        ))

        return {"status": "success", "email_id": email_id}

    except Exception as exc:
        raise self.retry(exc=exc)


if __name__ == "__main__":
    print("Testing Redis connection...")
    result = celery_app.control.ping(timeout=5)
    if result:
        print("Redis connected successfully")
    else:
        print("Could not connect to Redis - check your REDIS_URL in .env")