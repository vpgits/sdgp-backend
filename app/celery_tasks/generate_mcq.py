from celery_worker.celery_app import app
from app.api.summary import create_context_summary
from app.api.huggingface import generate_mcq
import logging


@app.task(name="generate_mcq")
def generate_mcq_worker(
        question_id, key_point_id, access_token, refresh_token
):
    generate_mcq_worker_helper(key_point_id, access_token, refresh_token)
    return {"message": "success"}


def generate_mcq_worker_helper(key_point_id: str, access_token: str,
                               refresh_token: str) -> None:
    try:
        create_context_summary(key_point_id, access_token, refresh_token)
        generate_mcq(key_point_id, access_token, refresh_token)
    except Exception as e:
        logging.error(str(e))
