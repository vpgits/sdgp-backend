FROM python:3.11.7-slim

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5555

CMD ["celery", "-A", "celery_worker.celery_app", "worker", "--loglevel=info"]