from celery_app.celery_app import app
import time


@app.task(name="ticktock")
def tick_tock_worker():
    time.sleep(20)
    print("tick-tock")
    return "tick-tock"
