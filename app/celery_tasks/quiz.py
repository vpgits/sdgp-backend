import logging
import os
import string
import requests
import json
from app.api.parse import get_pages
from app.config.supabase_client import get_supabase_client
from supabase import Client
from celery_worker.celery_app import app
from app.models.main import MCQ
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.task(bind=True, name="quiz")
def quiz_worker(self, quiz_id, access_token, refresh_token):
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        quiz_worker_helper(self, supabase_client, quiz_id)
        return {"message": "success"}
    except Exception as e:
        return {"message": f"failed: {str(e)}"}


def quiz_worker_helper(task, supabase: Client, quiz_id: str):
    try:
        data = supabase.from_("quiz").select("*").eq("id", quiz_id).execute()
        document_id = data.data[0]["document_id"]
        task.update_state(state="PROGRESS", meta={"status": "Getting pages"})
        pages = get_pages(supabase, document_id)
        task.update_state(state="PROGRESS", meta={"status": "Generating questions"})
        count = 0
        for page in pages[:5]:
            response = call_runpod_endpoint(page)
            if response.get("status") == "COMPLETED":
                llm_response = response.get("output")
                mcq = parse_runpod_response(llm_response)
                type(mcq)
                data = supabase.from_("questions").insert({"data": mcq}).execute()
                logging.info(data)
                question_id = data.data[0]["id"]
                data = (
                    supabase.from_("quizInstance")
                    .insert([{"quiz_id": quiz_id, "question_id": question_id}])
                    .execute()
                )
                count += 1
                task.update_state(
                    state="PROGRESS",
                    meta={"status": f"Completed {count}/{len(pages)} questions"},
                )
                supabase.from_("quiz").update({"generating": False}).eq(
                    "id", quiz_id
                ).execute()
            else:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "status": f"Failed to generate question {response.get('output')}"
                    },
                )
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
{\"type\": \"object\", \"properties\": {\"Output\": {\"type\": \"object\", \"properties\": {\"question\": {\"type\": \"string\"}, \"correct_answer\": {\"type\": \"string\"}, \"incorrect_answers\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"question\", \"correct_answer\", \"incorrect_answers\"]}}, \"required\": [\"Output\"]}
Task Objective:
Analyze the text to identify the core concept.
Formulate a question that encapsulates this concept.
Determine one correct answer and generate three plausible incorrect answers.
Adhere to the provided JSON schema for your output.
"""
                + f"### Input :{input_text.encode('utf-8')}.[/INST]"
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
