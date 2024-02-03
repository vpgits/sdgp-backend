from celery import Celery

app = Celery(
    "worker",
    # broker="pyamqp://guest@localhost//",  # Use the service name as defined in docker-compose.yml
    broker="pyamqp://sdgp_admin:59h@WeMyBtfV$YD@rabbitmq//",  # Use the service name as defined in docker-compose.yml
    backend="rpc://",
    include=[
        "celery_tasks.preprocess",
        "celery_tasks.generate_mcq",
        "celery_tasks.tick_tock",
        "celery_tasks.quiz",
    ],
)
app.conf.broker_connection_retry_on_startup = True
