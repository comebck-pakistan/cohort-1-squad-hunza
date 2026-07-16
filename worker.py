from celery import Celery

app = Celery("ai_worker")

@app.task
def example_task():
    return "Hello from Celery"
