import logging
import os
from supabase import Client
from app.api.embeddings import generate_embedding_query
from fastapi import HTTPException
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone.core.client.model.query_response import QueryResponse
from app.config.supabase_client import get_supabase_client
from app.api.parse import get_pages

load_dotenv()


def download_file(path: str, access_token: str, refresh_token: str):
    supabase: Client = get_supabase_client(access_token, refresh_token)
    file_path = f"./resources/{path}"
    try:
        res = supabase.storage.from_("public/pdf").download(path)
        logging.info("download_file reading")
        # if the ./resources folder does not exist, create it
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb+") as f:
            f.write(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_context(
        document_id: str, user_id: str, supabase_client: Client
):
    try:
        response = (
            supabase_client.table("documents")
            .select("summary")
            .eq("id", document_id)
            .execute()
        )
        key_points = response.data[0].get("summary").get("key_points")
        logging.info("key points extracted successfully!")

        for key_point in key_points:
            extract_context_for_query(key_point, document_id, user_id, supabase_client)
        logging.info("Content extracted successfully!")
    except Exception as e:
        logging.error(str(e))


def extract_context_for_query(key_point, document_id, user_id, supabase_client):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))

        key_point = generate_embedding_query(key_point)

        response = index.query(namespace=document_id, vector=key_point, top_k=5)
        context = extract_indexes(response, supabase_client, document_id)

        supabase_client.table("key_points").upsert(
            {
                "key_point": key_point,
                "document_id": document_id,
                "context": context,
                "user_id": user_id,
            }
        ).execute()
    except Exception as e:
        logging.error(str(e))


def extract_indexes(response: QueryResponse, supabase_client, document_id: str) -> str:
    context_index = []
    context: str = ""
    for r in response.matches:
        context_index.append(int(r.get("id").split(":")[1]))
    pages = get_pages(supabase_client, document_id)
    for i in context_index:
        context += pages[i]
    return context
