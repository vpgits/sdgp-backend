FROM python:3.11.7-slim

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

COPY . /usr/src/app

EXPOSE 5555

CMD ["celery", "-A", "celery_worker.celery_app", "worker", "--loglevel=info"]