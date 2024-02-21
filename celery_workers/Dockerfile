FROM python:3.11.7-slim

WORKDIR /usr/src/app
COPY ./celery_workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./celery_workers ./celery_workers
COPY ./celery_app   ./celery_app
EXPOSE 5555

CMD ["celery", "-A", "celery_app.celery_app:app", "worker", "--loglevel=info"]