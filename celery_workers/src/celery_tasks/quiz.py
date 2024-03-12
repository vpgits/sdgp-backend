from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
import logging
import celery
import json
from celery_workers.src.api.embeddings import get_similar_embeddings
from celery_workers.src.api.utils import sliding_window
from celery_workers.src.config.supabase_client import get_supabase_client
from supabase import Client
from celery_app.celery_app import app
from dotenv import load_dotenv

from celery_workers.src.api.database import (
    add_notification,
    get_pages_from_supabase,
    insert_key_points,
    insert_quiz_summary,
)
from celery_workers.src.api.helpers import (
    parse_openai_response,
    parse_runpod_response,
    update_task_state,
)
from celery_workers.src.api.requests import (
    create_key_points,
    generate_mcq_fireworks,
    generate_mcq_runpod,
    create_quiz_summary,
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.task(bind=True, name="quiz")
def quiz_worker(self: celery.Task, quiz_id, default_model, access_token, refresh_token):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        quiz_worker_helper(self, supabase_client, quiz_id, default_model)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


@app.task(bind=True, name="rapid-quiz")
def rapid_quiz_worker(
    self: celery.Task, quiz_id, default_model, access_token, refresh_token
):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        rapid_quiz_worker_helper(self, supabase_client, quiz_id, default_model)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


def rapid_quiz_worker_helper(
    task: celery.Task, supabase: Client, quiz_id: str, default_model: bool
):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        if not data.data:
            raise Exception("No quiz data found for the given quiz_id")
        document_id = data.data[0]["document_id"]
        update_task_state(task, "Getting pages")
        pages = get_pages_from_supabase(supabase, document_id)
        update_task_state(task, "Generating questions")
        pages = sliding_window(pages)
        default_model = data.data[0]["default_model"]
        if default_model:
            mcqs = generate_mcq_runopod_bulk(pages)
        else:
            mcqs = generate_mcq_openai_bulk(pages)
        if not mcqs:
            logging.error("Endpoint seems to be busy")
            update_task_state(
                task, "Endpoint seems to be busy", "FAILED"
            )  # Update the task state to indicate failure
            return
        update_task_state(task, "Inserting questions")
        bulk_insert_mcq(supabase, quiz_id, mcqs, document_id)
        supabase.from_("quiz").update({"generating": False}).eq("id", quiz_id).execute()
        update_task_state(task, "Creating quiz summary")
        create_quiz_summary_context(supabase, quiz_id, mcqs)
        add_notification(
            supabase,
            "Rapid Quiz",
            "Rapid Quiz generated successfully for quiz_id: {quiz_id}",
        )
    except Exception as e:
        update_task_state(task, "Failed")  # Update the task state to indicate failure
        logging.error(f"Error in rapid_quiz_worker_helper for quiz_id {quiz_id}: {e}")
        add_notification(supabase, "Rapid Quiz", f"Rapid Quiz generation failed: {e}")
        raise e


def bulk_insert_mcq(supabase: Client, quiz_id: str, mcqs: list[str], document_id: str):
    mcqs = [
        {"data": mcq, "quiz_id": quiz_id, "document_id": document_id} for mcq in mcqs
    ]
    supabase.from_("questions").insert(mcqs).execute()


def generate_mcq_runopod_bulk(pages: list[str]):

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_mcq_runpod, page) for page in pages]
            wait(futures, return_when=ALL_COMPLETED)
            results = [parse_runpod_response(future.result()) for future in futures]
            return results
    except Exception as e:
        raise e


def generate_mcq_openai_bulk(pages: list[str]):
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_mcq_fireworks, page) for page in pages]
            wait(futures, return_when=ALL_COMPLETED)
            results = [parse_openai_response(future.result()) for future in futures]
            return results
    except Exception as e:
        raise e


def quiz_worker_helper(
    task: celery.Task, supabase: Client, quiz_id: str, default_model: bool
):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        if not data.data:
            update_task_state(
                task, "No quiz data found for the given quiz_id", "FAILED"
            )
        document_id = data.data[0]["document_id"]
        num_of_questions = data.data[0]["num_of_questions"]
        remarks = data.data[0]["remarks"]
        update_task_state(task, "Getting pages")
        pages = get_pages_from_supabase(supabase, document_id)
        update_task_state(task, "Creating key points")
        logging.info("Creating key points")
        key_points = create_key_points(
            text=pages, subtext=remarks, num_of_questions=num_of_questions
        )
        insert_key_points(supabase, key_points, quiz_id)
        update_task_state(task, "Generating questions")
        key_points = json.loads(key_points).get("key_points")
        contexts = [
            get_similar_embeddings(key_point, document_id, pages)
            for key_point in key_points
        ]
        default_model = data.data[0]["default_model"]
        if default_model:
            mcqs = generate_mcq_runopod_bulk(contexts)
        else:
            mcqs = generate_mcq_openai_bulk(contexts)
        if not mcqs:
            logging.error("Endpoint seems to be busy")
            update_task_state(
                task, "Endpoint seems to be busy", "FAILED"
            )  # Update the task state to indicate failure
            return
        update_task_state(task, "Inserting questions")
        bulk_insert_mcq(supabase, quiz_id, mcqs, document_id)
        supabase.from_("quiz").update({"generating": False}).eq("id", quiz_id).execute()
        update_task_state(task, "Creating quiz summary")
        create_quiz_summary_context(supabase, quiz_id, mcqs)
        add_notification(
            supabase, "Quiz", f"Quiz generated successfully for quiz_id: {quiz_id}"
        )
    except Exception as e:
        update_task_state(task, "Failed")  # Update the task state to indicate failure
        logging.error(f"Error in quiz_worker_helper: {e}")
        add_notification(
            supabase, "Quiz", f"Quiz generation failed for quiz_id {quiz_id}: {e}"
        )


def create_quiz_summary_context(
    supabase_client: Client, quiz_id: str, questions: list[str]
):
    try:
        response = create_quiz_summary(questions)
        insert_quiz_summary(supabase_client, quiz_id, response)
    except Exception as e:
        raise e
