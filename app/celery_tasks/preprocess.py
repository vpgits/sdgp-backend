from celery_worker.celery_app import app
from app.api.database import extract_context
from app.config.supabase_client import get_supabase_client, get_current_user
from app.api.parse import parse_pdf_pages, does_pages_exist, get_pages, sliding_window
from app.api.embeddings import create_vector_index
from app.api.summary import create_summary_json
from supabase import Client
import logging
import os

logger = logging.getLogger(__name__)


@app.task(name="preprocess")
def preprocess_worker(path, document_id, access_token, refresh_token):
    # this function will parse an entire pdf into an array of pages, then push to database
    try:
        supabase_client: Client = get_supabase_client(access_token, refresh_token)
        user_id: str = get_current_user(supabase_client, access_token)
        preprocess_worker_helper(supabase_client, path, document_id, user_id)
        return {"message": "success"}
    except Exception as e:
        logger.error("An exception has occurred on preprocess_worker: {str(e)}")
        return {"message": f"failed: {str(e)}"}
    finally:
        if os.path.exists(f"./resources/{path}"):
            os.remove(f"./resources/{path}")


def preprocess_worker_helper(supabase_client: Client, path: str, document_id: str, user_id: str):
    try:
        if not does_pages_exist(supabase_client, document_id):
            logger.info("Pages do not exist. Extracting pages from PDF")
            parse_pdf_pages(path, supabase_client, document_id)
        pages = get_pages(supabase_client, document_id)
        if pages:
            create_vector_index(pages, document_id)
            create_summary_json(pages, document_id, user_id, supabase_client)
            extract_context(document_id, user_id, supabase_client)
    except Exception as e:
        logger.error(f"An exception has occurred on preprocess_worker_helper: {str(e)}")
        raise e
