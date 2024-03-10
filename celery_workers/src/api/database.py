import logging
import os
import json
from supabase import Client
from celery_workers.src.api.embeddings import generate_embedding_query
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone.core.client.model.query_response import QueryResponse
from celery_workers.src.api.utils import sliding_window

load_dotenv()


def download_file(path: str, supabase_client: Client):
    file_path = f"./resources/{path}"
    try:
        res = supabase_client.storage.from_("pdf").download(path)
        # if the ./resources folder does not exist, create it
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb+") as f:
            f.write(res)
    except Exception as e:
        logging.error("Error Downloading file: " + str(e))
        raise e


def extract_context(document_id: str, user_id: str, supabase_client: Client):
    try:
        response = (
            supabase_client.table("documents")
            .select("summary")
            .eq("id", document_id)
            .execute()
        )
        key_points = response.data[0].get("summary").get("key_points")
        logging.info("key points extracted successfully!")
        if does_extracted_context_exist(document_id,supabase_client):
            logging.info("Context already exists!")
            return
        for key_point in key_points:
            extract_context_for_query(key_point, document_id, user_id, supabase_client)
        logging.info("Content extracted successfully!")
    except Exception as e:
        logging.error(str(e))


def does_extracted_context_exist(
    document_id: str,supabase_client: Client
) -> bool:
    try:
        response = (
            supabase_client.table("key_points")
            .select("context")
            .eq("document_id", document_id)
            .execute()
        )
        if not response.data[0].get("context"):
            return False
        else:
            return True
    except Exception as e:
        logging.error(str(e))


def extract_context_for_query(key_point, document_id, user_id, supabase_client):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))

        key_point_embedding = generate_embedding_query(key_point)

        response = index.query(
            namespace=document_id, vector=key_point_embedding, top_k=5
        )
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
    pages = get_pages_from_supabase(supabase_client, document_id)
    pages = sliding_window(pages)
    for i in context_index:
        context += pages[i]
    logging.info("context: " + context)
    return context


def insert_quiz_summary(supabase_client: Client, quiz_id: str, summary: str):
    supabase_client.from_("quiz").update({"summary": json.loads(summary)}).eq(
        "id", quiz_id
    ).execute()


def set_quiz_generating_state(supabase: Client, quiz_id: str, state: bool):
    supabase.from_("quiz").update({"generating": state}).eq("id", quiz_id).execute()


def insert_key_points(supabase: Client, key_points: list[str], quiz_id: str):
    supabase.from_("key_points").insert(
        {"data": json.loads(key_points), "quiz_id": quiz_id}
    ).execute()


def add_pages_to_supabase(
    supabase_client: Client, pages: list[str], document_id: str
) -> None:
    supabase_client.table("documents").update({"data": {"data": pages}}).eq(
        "id", document_id
    ).execute()
    logging.info("Pages added successfully!")


def get_pages_from_supabase(supabase: Client, document_id: str) -> list[str]:
    data = supabase.from_("documents").select("data").eq("id", document_id).execute()
    pages = data.data[0].get("data").get("data")
    logging.info("Pages retrieved successfully!")
    return pages
