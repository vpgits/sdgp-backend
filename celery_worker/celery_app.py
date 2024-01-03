from celery import Celery

app = Celery(
    "worker",
    broker="pyamqp://guest@localhost//",  # Use pyamqp for RabbitMQ
    backend="rpc://",  # Use RPC as the result backend
    include=["app.celery_tasks.parse_pdf"]
)
