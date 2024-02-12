from celery_app.celery_app import app
from celery.app.task import Task
import time


@app.task(bind=True, name="ticktock")
def tick_tock_worker(self: Task, *args, **kwargs):
    for i in range(100):
        time.sleep(1)
        self.update_state(state="PROGRESS", meta={"status": f"tick-tock-{i}"})
        print("tick-tock")
    return "tick-tock"
