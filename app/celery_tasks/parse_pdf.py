import asyncio
import logging
import os
import time
import json
import aiohttp
from app.api.database import extract_context
from app.config.supabase_client import get_supabase_client
from celery_worker.celery_app import app
from app.api.create_summary import create_context_summary
from app.api.create_summary import create_summary_json
from app.api.parse_pdf import parse_pdf_pages, does_pages_exist, get_pages, sliding_window
from app.api.create_embeddings import create_vector_index


@app.task(name="parse_pdf")
def parse_pdf_worker(path, document_id, user_id, access_token, refresh_token):
    # this function will parse an entire pdf into an array of pages, then push to database
    try:
        supabase_client = get_supabase_client(access_token, refresh_token)
        supabase_client.auth.get_session()
        if does_pages_exist(supabase_client, document_id):
            logging.info("Pages already exists!")
        else:
            parse_pdf_pages(path, supabase_client, document_id)
        pages = get_pages(supabase_client, document_id)
        logging.info(pages)
        create_vector_index(sliding_window(pages), document_id)
        create_summary_json(pages, document_id, user_id, supabase_client)
        extract_context(document_id, user_id, supabase_client)
        return {"message": "success"}
    except Exception as e:
        print(str(e))
        return {"message": f"failed: {str(e)}"}
    finally:
        if os.path.exists(f"./resources/{path}"):
            os.remove(f"./resources/{path}")


@app.task(name="generate_mcq")
def generate_mcq_worker(
    document_id, key_point_id, user_id, access_token, refresh_token
):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        generate_mcq_worker_helper(
            document_id, key_point_id, user_id, access_token, refresh_token
        )
    )


async def generate_mcq_worker_helper(
    document_id, key_point_id, user_id, access_token, refresh_token
):
    try:
        await create_context_summary(
            document_id, key_point_id, access_token, refresh_token
        )
        supabase = get_supabase_client(access_token, refresh_token)
        response = (
            supabase.table("key_points")
            .select("key_point", "summary")
            .eq("id", key_point_id)
            .execute()
        )
        key_point = response.data[0].get("key_point")
        context = response.data[0].get("summary")
        url = "https://api.runpod.ai/v2/sxtsfzuyap0dvk/runsync"

        payload = json.dumps(
            {
                "input": {
                    "text": "### Instructions: Generate three multiple MCQ questions and correct answer and incorrect "
                    "answers from the given context. The question should be general purpose and should be "
                    "answerable without the context. Output should be an array of JSON, containing questions and "
                    "answers in the below "
                    'format.\n[\n  {\n    "question": "string",\n    "correct_answer": "string",\n    '
                    '"incorrect_answers": ["string", "string", "string"]\n  },\n]\n### Context:'
                    f"### Context: {context}" + f"### Output :\n",
                }
            }
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer P388SJ04GD6ZE9LE6GV1TOMCVV6SVTHHITBR5199",
            "Cookie": "__cflb=02DiuEDmJ1gNRaog7BudgwPAUzGWrv7SjG8EW9eaypptc",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as response:
                response = await response.json()
        logging.info(response)
        response = response.get("output")
        mcqs = extract_json_array_from_response(response)
        for mcq in mcqs:
            logging.info(mcq)
            supabase = get_supabase_client(access_token, refresh_token)
            supabase.table("questions").insert(
                {"data": mcq, "document_id": document_id, "user_id": user_id}
            ).execute()
            logging.info("MCQ added successfully!")
    except Exception as e:
        logging.error(str(e))


def extract_json_array_from_response(response):
    try:
        start_index = response.find("\n### Output :\n")
        logging.info("start index here" + str(start_index))
        text = response[start_index:]
        text = text.replace("\n### Output :\n", "")
        return json.loads(text)
    except Exception as e:
        logging.error("extract json from response: " + str(e))


@app.task(name="tick-tock")
def tick_tock_worker():
    time.sleep(5)
    print("tick-tock")
    return "tick-tock"



