import json
import requests
from dotenv import load_dotenv
import os
from app.api.database import get_supabase_client
from supabase import Client
import logging

load_dotenv()

API_URL = os.getenv("HUGGINGFACE_ENDPOINT_URL")
API_KEY = os.getenv("HUGGINGFACE_SECRET")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def generate_mcq(question_id, key_point_id, access_token, refresh_token):
    logging.info("Attempting to generate mcq")
    supabase_client: Client = get_supabase_client(access_token, refresh_token)
    response = (
        supabase_client.table("key_points")
        .select("context")
        .eq("id", key_point_id)
        .execute()
    )
    text = response.data[0].get("context")
    payload = {
        "inputs": "### Instruction : You are given a sequence of text. Summarize its context. From that summary generate a logical question, correct answer "
        "and three incorrect answers suitable for mcq. The output should be formatted as "
        "a json in the below format."
        + '{"type": "object", "properties": {"Output": {"type": '
        '"object", "properties": {"question": {"type": "string"}, '
        '"correct_answer": {"type": "string"}, "incorrect_answers": '
        '{"type": "array", "items": {"type": "string"}}}, '
        '"required": ["question", "correct_answer", '
        '"incorrect_answers"]}}, "required": ["Output"]}'
        f"### Input : {text}### Output :",
        "parameters": {"max_new_tokens": 128, "return_full_text": False},
    }

    response = query(payload)
    output_json = json.loads(response[0]["generated_text"]).get("Output")

    supabase_client.table("questions").upsert(
        {
            "data": output_json,
        }
    ).eq("id", question_id).execute()
