from celery import Celery

app = Celery(
    "worker",
    # broker="pyamqp://guest@localhost//",  # Use the service name as defined in docker-compose.yml
    broker="pyamqp://guest@rabbitmq//",  # Use the service name as defined in docker-compose.yml
    backend="rpc://",
    include=["app.celery_tasks.preprocess", "app.celery_tasks.generate_mcq", "app.celery_tasks.tick_tock"],
)
app.conf.broker_connection_retry_on_startup = True