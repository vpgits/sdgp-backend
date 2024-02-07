from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

app = Celery(
    "worker",
    # broker="pyamqp://guest@localhost//",  # Use the service name as defined in docker-compose.yml
    broker=os.getenv(
        "BROKER_URL"
    ),  # Use the service name as defined in docker-compose.yml
    backend="rpc://",
    include=[
        "celery_tasks.preprocess",
        "celery_tasks.generate_mcq",
        "celery_tasks.tick_tock",
        "celery_tasks.quiz",
    ],
)
app.conf.broker_connection_retry_on_startup = True
