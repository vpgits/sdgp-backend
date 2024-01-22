import json
import logging
from openai import OpenAI
from supabase import Client
from app.config.supabase_client import get_supabase_client


def create_summary_json(
        text: str, document_id: str, user_id: str, supabase_client: Client, subtext=None
):
    # this openai function takes in a string and outputs a summary gpt-4-1106-preview
    try:
        summary = (
            supabase_client.table("documents")
            .select("summary")
            .eq("id", document_id)
            .execute()
        )
        logging.info(summary)
        if summary.data[0].get("summary") is not None:
            logging.info("Summary already exists!")
        else:
            logging.info("Attempting to generate summary")
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": """You are to find key points at a user given text. 
                                                                text are from lecture materials. refrain from including personal
                                                                information or any other information that is not related to
                                                                the subject as key points. key points should be simple.
                                                                Return a JSON. The JSON should only have an 
                                                                array with only label called "key_points" """,
                    },
                    {"role": "user", "content": f"{text}. {subtext}" ""},
                ],
            )

            # execute_query("INSERT INTO public.documents (summary, document_id, user_id) VALUES (%s, %s, %s)")
            response = (
                supabase_client.table("documents")
                .upsert(
                    {
                        "summary": json.loads(response.choices[0].message.content),
                        "id": document_id,
                        "user_id": user_id,
                    }
                )
                .execute()
            )
            logging.info(f"Summary added successfully! document_id: {document_id}")
        return True
    except Exception as e:
        logging.error(str(e))
        return False


async def create_context_summary(
        document_id: str, key_point_id: str, access_token: str, refresh_token: str
):
    try:
        supabase: Client = get_supabase_client(access_token, refresh_token)
        response = (
            supabase.table("key_points")
            .select("context", "key_point", "summary")
            .eq("id", key_point_id)
            .execute()
        )
        logging.info(response)
        summary = response.data[0].get("summary")
        context = response.data[0].get("context")
        logging.info("Context extracted successfully!")
        key_point = response.data[0].get("key_point")
        if summary is None:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": f"""Create a concise, educational short note 
                                                                     on the following topic: {key_point} The note
                                                                      should be standalone, focusing solely on key
                                                                       educational content relevant to the topic. It should
                                                                        be structured to clearly present the essential 
                                                                        concepts, definitions, or principles related to the 
                                                                        topic in a manner that is easy to understand. The
                                                                         note should be brief yet informative, ideally 
                                                                         fitting into a single paragraph, and should avoid 
                                                                         any contextual or unrelated information. 
                                                                    Return a JSON. The JSON should only have a 
                                                                     label called "summary" """,
                    },
                    {"role": "user", "content": f"{context}. "},
                ],
            )
            summary = json.loads(response.choices[0].message.content).get("summary")
            logging.info("Summary generated successfully!")
        else:
            logging.info("Summary already exists!")
        supabase.table("key_points").update(
            {
                "summary": summary,
            }
        ).eq("id", key_point_id).execute()
        logging.info("Summary added successfully!")
    except Exception as e:
        logging.error(str(e))

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
