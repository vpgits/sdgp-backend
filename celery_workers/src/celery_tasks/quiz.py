import logging
from multiprocessing import context
import os
from typing import ByteString
import requests
import json
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
def rapid_quiz_worker(self, quiz_id, access_token, refresh_token):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        rapid_quiz_worker_helper(self, supabase_client, quiz_id)
        supabase_client.auth.sign_out()
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


def rapid_quiz_worker_helper(task, supabase: Client, quiz_id: str):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        document_id = data.data[0]["document_id"]
        task.update_state(state="PROGRESS", meta={"status": "Getting pages"})
        pages = get_pages(supabase, document_id)
        task.update_state(state="PROGRESS", meta={"status": "Generating questions"})
        count = 0
        pages = sliding_window(pages)
        for page in pages:
            response = call_runpod_endpoint(page)
            if response.get("status") == "COMPLETED":
                llm_response = response.get("output")
                logging.info(llm_response)
                mcq = parse_runpod_response(llm_response)
                # type(mcq)
                supabase.from_("questions").insert(
                    {"data": mcq, "quiz_id": quiz_id, "document_id": document_id}
                ).execute()
                count += 1
                task.update_state(
                    state="PROGRESS",
                    meta={"status": f"Completed {count}/{len(pages)} questions"},
                )
            else:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "status": f"Failed to generate question {response.get('output')}"
                    },
                )
        supabase.from_("quiz").update({"generating": False}).eq("id", quiz_id).execute()
    except Exception as e:
        raise e


def quiz_worker_helper(task, supabase: Client, quiz_id: str):
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
        supabase.from_("key_points").insert(
            {"data": key_points, "quiz_id": quiz_id}
        ).execute()
        task.update_state(state="PROGRESS", meta={"status": "Generating questions"})
        key_points = json.loads(key_points).get("key_points")
        count = 0
        for key_point in key_points:
            context = get_similar_embeddings(key_point, document_id, pages)
            response = call_runpod_endpoint(context)
            if response.get("status") == "COMPLETED":
                llm_response = response.get("output")
                mcq = parse_runpod_response(llm_response)
                type(mcq)
                supabase.from_("questions").insert(
                    {"data": mcq, "quiz_id": quiz_id, "document_id": document_id}
                ).execute()
                count += 1
                task.update_state(
                    state="PROGRESS",
                    meta={"status": f"Completed {count}/{len(key_points)} questions"},
                )
            else:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "status": f"Failed to generate question {response.get('output')}"
                    },
                )
        supabase.from_("quiz").update({"generating": False}).eq("id", quiz_id).execute()
    except Exception as e:
        raise e


def call_runpod_endpoint(input_text: str):
    url = f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_WORKER_ID')}/runsync"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.getenv("RUNPOD_API_KEY"),
        "charset": "utf-8",
    }

    payload = {
        "input": {
            "text": str(
                """[INST]### Instruction : Generate a multiple-choice question (MCQ) based on the core concept identified in a given text. This MCQ should include one correct answer and three incorrect but plausible answers, crafted to assess comprehension of the concept. Format your output as a JSON object following a specified schema, emphasizing the logical extraction and representation of the text's main idea through a question and answers format. This task requires understanding and distilling the essence of the input text, applying it to create an educational or evaluative MCQ relevant to the discussed concept.
Output Format Schema:
The output should be a JSON object with a specific structure, including fields for the question, the correct answer, and an array of incorrect answers, all requiring strings.
Task Objective:
Analyze the text to identify the core concept.
Formulate a question that encapsulates this concept.
Determine one correct answer and generate three plausible incorrect answers.
Adhere to the provided JSON schema for your output. Make sure not to generate escape characters.
.The output should be formatted as a json in the below format." + "{\"type\": \"object\", \"properties\": {\"Output\": {\"type\": \"object\", \"properties\": {\"question\": {\"type\": \"string\"}, \"correct_answer\": {\"type\": \"string\"}, \"incorrect_answers\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"question\", \"correct_answer\", \"incorrect_answers\"]}}, \"required\": [\"Output\"]}"""
                + f"### Input :{input_text}.[/INST]"
                + "### Output :"
            )
        }
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    return response.json()


def parse_runpod_response(llm_response: str) -> str:
    special_token = "### Output :"
    output_start = llm_response.find(special_token) + len(special_token)
    if output_start > len(special_token):
        json_str = llm_response[output_start:].strip()
        output_json = json.loads(json_str)
        mcq = output_json.get("Output")
        return mcq


# """[INST]### Instruction : Generate a multiple-choice question (MCQ) based on the core concept identified in a given text. This MCQ should include one correct answer and three incorrect but plausible answers, crafted to assess comprehension of the concept. Format your output as a JSON object following a specified schema, emphasizing the logical extraction and representation of the text's main idea through a question and answers format. This task requires understanding and distilling the essence of the input text, applying it to create an educational or evaluative MCQ relevant to the discussed concept.
# Output Format Schema:
# The output should be a JSON object with a specific structure, including fields for the question, the correct answer, and an array of incorrect answers, all requiring strings.
# {\"type\": \"object\", \"properties\": {\"Output\": {\"type\": \"object\", \"properties\": {\"question\": {\"type\": \"string\"}, \"correct_answer\": {\"type\": \"string\"}, \"incorrect_answers\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"question\", \"correct_answer\", \"incorrect_answers\"]}}, \"required\": [\"Output\"]}
# Task Objective:
# Analyze the text to identify the core concept.
# Formulate a question that encapsulates this concept.
# Determine one correct answer and generate three plausible incorrect answers.
# Adhere to the provided JSON schema for your output.
# """
