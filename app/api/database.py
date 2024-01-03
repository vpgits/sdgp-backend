import os
from supabase import create_client, Client
from app.api.create_embeddings import generate_embedding_query
import json
import psycopg2
from fastapi import HTTPException
from app.api.create_mcq import create_mcq_json
from dotenv import load_dotenv

from app.config.supabase_client import get_supabase

load_dotenv()


def download_file(path: str):
    supabase: Client = get_supabase()
    file_path = f"./resources/{path}"
    res = supabase.storage.from_('public/pdf').download(path)
    # Write the downloaded content to a file
    try:
        # if the ./resources folder does not exist, create it
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb+') as f:
            f.write(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def execute_query(query, params=None):
    # this is a simple prostgresql query function
    DB_CONNECTION = os.getenv('DB_CONNECTION')
    conn = psycopg2.connect(DB_CONNECTION)
    with conn.cursor() as cur:
        cur.execute(query, params)
        if query.lower().strip().startswith("select"):
            return cur.fetchall()
        conn.commit()
        return None


async def cosine_similarity_query(query):
    # this will return an array of similar text from the embedding table
    embedding = await generate_embedding_query(query)
    embedding = embedding.get("embedding")
    query = """SELECT body FROM public.embeddings ORDER BY embedding <=> '{query_embedding}' LIMIT 5"""
    return await execute_query(query)


async def load_mcq(key_point, context, document_id=1):
    question_json = create_mcq_json(key_point, context)
    insert_query = f" INSERT INTO public.questions (data, document_id) VALUES (%s, 1)"
    execute_query(insert_query, (json.dumps(question_json),))
