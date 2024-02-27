from celery_app.celery_app import app
from celery_workers.src.api.database import extract_context
from celery_workers.src.config.supabase_client import (
    get_supabase_client,
    get_current_user,
)
from celery_workers.src.api.parse import (
    create_document_summary_context,
    parse_pages,
    does_pages_exist,
    get_pages,
)
from celery_workers.src.api.embeddings import create_vector_index
from supabase import Client
import logging
import os
from celery_app.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True, name="preprocess")
def preprocess_worker(self, path, document_id, access_token, refresh_token):
    # this function will parse an entire pdf into an array of pages, then push to database
    try:
        supabase_client: Client = get_supabase_client(access_token, refresh_token)
        user_id: str = get_current_user(supabase_client, access_token)
        preprocess_worker_helper(self, supabase_client, path, document_id, user_id)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        logger.error("An exception has occurred on preprocess_worker: {str(e)}")
        return {"message": f"failed: {str(e)}"}
    finally:
        if os.path.exists(f"./resources/{path}"):
            os.remove(f"./resources/{path}")


def preprocess_worker_helper(
    task, supabase_client: Client, path: str, document_id: str, user_id: str
):
    try:
        if not does_pages_exist(supabase_client, document_id):
            logger.info("Pages do not exist. Extracting pages from PDF")
            task.update_state(
                state="PROGRESS", meta={"status": "Extracting pages from PDF"}
            )
            parse_pages(path, supabase_client, document_id)
        pages = get_pages(supabase_client, document_id)
        if pages:
            task.update_state(
                state="PROGRESS", meta={"status": "Creating vector index"}
            )
            create_vector_index(pages, document_id)
            task.update_state(state="PROGRESS", meta={"status": "Creating summary"})
            create_document_summary_context(pages, supabase_client, document_id)
            return {"message": "success"}
    except Exception as e:
        logger.error(f"An exception has occurred on preprocess_worker_helper: {str(e)}")
        return {"message": f"failed: {str(e)}"}
