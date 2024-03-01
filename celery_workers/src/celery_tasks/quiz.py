import logging
import celery
import json
from celery_workers.src.api.database import (
    insert_key_points,
    insert_quiz_summary,
    set_quiz_generating_state,
)
from celery_workers.src.api.helpers import (
    cancel_runpod_request,
    parse_runpod_response,
    update_task_state,
)
from celery_workers.src.api.requests import (
    generate_mcq_fireworks,
    generate_mcq_runpod,
    create_quiz_summary,
)
from celery_workers.src.api.parse import get_pages, sliding_window
from celery_workers.src.api.embeddings import (
    get_similar_embeddings,
)
from celery_workers.src.api.summary import create_key_points_json
from celery_workers.src.config.supabase_client import get_supabase_client
from supabase import Client
from celery_app.celery_app import app
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.task(bind=True, name="quiz")
def quiz_worker(self, quiz_id, access_token, refresh_token):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        quiz_worker_helper(self, supabase_client, quiz_id)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


@app.task(bind=True, name="rapid-quiz")
def rapid_quiz_worker(self: celery.Task, quiz_id, access_token, refresh_token):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        rapid_quiz_worker_helper(self, supabase_client, quiz_id)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


def rapid_quiz_worker_helper(task: celery.Task, supabase: Client, quiz_id: str):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        document_id = data.data[0]["document_id"]
        update_task_state(task, "Getting pages")
        pages = get_pages(supabase, document_id)
        update_task_state(task, "Generating questions")
        pages = sliding_window(pages)
        questions = []
        mcqs = generate_mcq_runopod_bulk(pages, task)
        bulk_insert_mcq(supabase, quiz_id, mcqs, document_id)
        supabase.from_("quiz").update({"generating": False}).eq("id", quiz_id).execute()
        create_quiz_summary_context(supabase, quiz_id, questions)
    except Exception as e:
        raise e


def bulk_insert_mcq(supabase: Client, quiz_id: str, mcqs: list[str], document_id: str):
    mcqs = [
        {"data": mcq, "quiz_id": quiz_id, "document_id": document_id} for mcq in mcqs
    ]
    supabase.from_("questions").insert(mcqs).execute()


def generate_mcq_runopod_bulk(pages: list[str], task: celery.Task):
    count = 0
    questions = []
    for page in pages:
        response = generate_mcq_runpod(page)
        if response.get("status") == "COMPLETED":
            llm_response = response.get("output")
            logging.info(llm_response)
            mcq = parse_runpod_response(llm_response)
            task.update_state(
                state="PROGRESS",
                meta={"status": f"Completed {count}/{len(pages)} questions"},
            )
            questions.append(mcq)
        elif response.get("status") == "IN_QUEUE":
            task.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Failed to generate question {response.get('output')}"
                },
            )
            response_id = response.get(id)
            cancel_runpod_request(response_id)
            # redirecting to fireworks
            questions = questions.extend(generate_mcq_fireworks_bulk(pages, task))
            break
    return questions


def generate_mcq_fireworks_bulk(pages: list[str], task: celery.Task):
    count = 0
    questions = []
    for page in pages:
        response = generate_mcq_fireworks(page)
        logging.info(response)
        mcq = parse_runpod_response(response)
        task.update_state(
            state="PROGRESS",
            meta={"status": f"Completed {count}/{len(pages)} questions"},
        )
        questions.append(mcq)
    return questions


def quiz_worker_helper(task: celery.Task, supabase: Client, quiz_id: str):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        document_id = data.data[0]["document_id"]
        num_of_questions = data.data[0]["num_of_questions"]
        remarks = data.data[0]["remarks"]

        task.update_state(state="PROGRESS", meta={"status": "Getting pages"})
        pages = get_pages(supabase, document_id)
        task.update_state(state="PROGRESS", meta={"status": "Creating key points"})
        key_points = create_key_points_json(
            text=pages, subtext=remarks, num_of_questions=num_of_questions
        )
        insert_key_points(supabase, key_points, quiz_id)
        task.update_state(state="PROGRESS", meta={"status": "Generating questions"})
        key_points = json.loads(key_points).get("key_points")
        count = 0
        questions = []
        for key_point in key_points:
            context = get_similar_embeddings(key_point, document_id, pages)
            response = generate_mcq_runpod(context)
            mcq = parse_runpod_response(response)
            type(mcq)
            count += 1
            task.update_state(
                state="PROGRESS",
                meta={"status": f"Completed {count}/{len(key_points)} questions"},
            )
            questions.append(mcq)
        bulk_insert_mcq(supabase, quiz_id, questions, document_id)
        set_quiz_generating_state(supabase, quiz_id, False)
        create_quiz_summary_context(supabase, quiz_id, questions)
    except Exception as e:
        raise e


def create_quiz_summary_context(
    supabase_client: Client, quiz_id: str, questions: list[str]
):
    try:
        response = create_quiz_summary(questions)
        insert_quiz_summary(supabase_client, quiz_id, response)
    except Exception as e:
        raise e
