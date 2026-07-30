"""
INGEST-01 follow-up: Gmail push subscriptions (users.watch) expire after a
maximum of 7 days and must be renewed, or notifications silently stop
arriving - the mailbox would look "connected" but nothing would come in
anymore. This renews every active connection's watch.

Not required for the webhook to work today - only needed for it to keep
working unattended past 7 days. Optional to wire up; run manually or via
Celery beat once worker.py's Celery setup is actually in use for the rest
of the pipeline too.

Manual run (no Celery needed):
    python -c "from tasks.gmail_watch_renewal import renew_all_watches_sync; renew_all_watches_sync()"

Via Celery beat (once worker.py is running things for real), add to
worker.py:
    from celery.schedules import crontab
    app.conf.beat_schedule = {
        "renew-gmail-watches-daily": {
            "task": "tasks.gmail_watch_renewal.renew_all_watches_task",
            "schedule": crontab(hour=3, minute=0),  # once a day is plenty for a 7-day expiry
        },
    }
"""
import asyncio
import logging

from app.modules.gmail_integration import repository as repo
from app.modules.gmail_integration.service import start_watch
from worker import app as celery_app

logger = logging.getLogger("tasks.gmail_watch_renewal")


async def _renew_all_watches() -> dict:
    connections = repo.list_all_active_connections()
    renewed, failed = 0, 0

    for connection in connections:
        try:
            await start_watch(connection["id"], connection["user_id"])
            renewed += 1
        except Exception as e:
            failed += 1
            logger.warning("Failed to renew watch for connection_id=%s: %s", connection["id"], e)

    return {"total": len(connections), "renewed": renewed, "failed": failed}


def renew_all_watches_sync() -> dict:
    """Plain sync entrypoint - no Celery required, just run the file/function directly."""
    return asyncio.run(_renew_all_watches())


@celery_app.task(name="tasks.gmail_watch_renewal.renew_all_watches_task")
def renew_all_watches_task():
    result = asyncio.run(_renew_all_watches())
    logger.info("Gmail watch renewal: %s", result)
    return result
