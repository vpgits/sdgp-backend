# Use an official Python runtime as a parent image
FROM python:3.11.7-slim


WORKDIR /usr/src/app
COPY ./fastapi_app/requirements.txt .
RUN pip install -r requirements.txt
COPY ./fastapi_app/src .
COPY ./celery_app ./celery_app
EXPOSE 8000


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
