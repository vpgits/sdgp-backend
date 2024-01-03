import asyncio
import json
import logging

from openai import OpenAI
from app.config.supabase_client import get_supabase
from supabase import Client
from pydantic import BaseModel


class APIResponse(BaseModel):
    data: list
    count: None


async def create_summary_json(text, document_id, user_id, subtext=None):
    # this openai function takes in a string and outputs a summary
    try:
        client = OpenAI()
        response = client.chat.completions.create(model="gpt-4-1106-preview",
                                                  response_format={"type": "json_object"},
                                                  messages=[{"role": "system",
                                                             "content": """You are to find key points at a user given text.
                                                              Return a JSON. The JSON should only have an 
                                                             array with only label called "key_points" """},
                                                            {"role": "user",
                                                             "content": f"{text}. {subtext}"""}])

        supabase: Client = get_supabase()
        # execute_query("INSERT INTO public.documents (summary, document_id, user_id) VALUES (%s, %s, %s)")
        response = supabase.table('documents').upsert(
            {
                "summary": json.loads(response.choices[0].message.content),
                "document_id": document_id,
                "user_id": user_id
            }
        ).execute()
        logging.info(f"Summary added successfully! document_id: {document_id}")
        return True
    except Exception as e:
        logging.error(str(e))
        return False


# async def create_cumulative_summary_json(chunks, document_id, user_id):
#     key_points = []
#     logging.info("Attempting to generate page summaries")
#     page_summaries = await asyncio.gather(*(create_summary_json(text=chunk) for chunk in chunks))
#     logging.info("Attempting to generate cumulative page summaries")
#     for page_summary in page_summaries:
#         key_points.extend(json.loads(page_summary).get("key_points"))
#     key_points = await create_summary_json(key_points)
#     supabase: Client = get_supabase()
#     # execute_query("INSERT INTO public.documents (summary, document_id, user_id) VALUES (%s, %s, %s)")
#     response = supabase.table('documents').upsert(
#         {
#             "summary": key_points,
#             "document_id": document_id,
#             "user_id": user_id
#         }
#     ).execute()
#     if isinstance(response, APIResponse):
#         return True
#     else:
#         return False

# async def create_summary_json_fireworks(text): fireworks.client.api_key = "" completion =
# fireworks.client.ChatCompletion.create( model="accounts/fireworks/models/llama-v2-70b-chat", messages=[ {"role":
# "system", "content": """You are to find key points at a user given text. Return only a JSON. The JSON should only
# have an array with only label called "key_points" Here is the schema.{ "$schema":
# "http://json-schema.org/draft-07/schema#", "type": "array", "items": { "type": "object", "properties": { "id": {
# "type": "string" }, "description": { "type": "string" } }, "required": ["id", "description"] } } """},
# {"role": "user", "content": f"{text}. Return only a JSON. I am parsing the output so no greet text"""} ],
# stream=False, n=1, max_tokens=4096, temperature=0.1, top_p=0.9, ) return completion.choices[0].message.content
