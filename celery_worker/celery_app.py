from celery import Celery

app = Celery(
    "worker",
    # broker="pyamqp://guest@rabbitmq//",  # Use the service name as defined in docker-compose.yml
    broker="pyamqp://guest@localhost//",  # Use the service name as defined in docker-compose.yml
    backend="rpc://",
    include=["app.celery_tasks.parse_pdf"],
)
app.conf.broker_connection_retry_on_startup = True