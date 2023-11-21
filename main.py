import asyncio
import json
import os
import re
from io import BytesIO
import aiohttp
import psycopg2
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from create_mcq import create_mcq_json
from create_summary import create_summary_json

# from app.database.document import upload_pdf
# from pdf_processing.parse import pdf_to_pages

app = FastAPI()
load_dotenv()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# @app.post("/parse")
# async def parse_pdf(file: bytes = File(...)):
#     try:
#         pages = await pdf_to_pages(file)
#         return {"data": pages}
#     except Exception as e:
#         return {"error": str(e)}, 500


# @app.post("/uploadfile/")
# async def create_upload_file(file: bytes = File(...)):
#     try:
#         # Assuming upload_pdf is a predefined function that processes the file
#         response = await upload_pdf(file)
#         return {"response": response}
#     except Exception as e:
#         # Raise a HTTPException with status code 500
#         raise HTTPException(status_code=500, detail=str(e))


# write me a post function that returns a byte stream of a file

@app.post("/parse_pdf_pages/")
async def parse_pdf_pages():
    # this function will parse an entire pdf into an array of pages
    try:
        with open('sample.pdf', 'rb') as f:
            response = f.read()
        reader = PdfReader(BytesIO(response))
        pages = []
        for page in reader.pages:
            cleaned_page = re.sub(r"\s+", " ", page.extract_text())
            pages.append(cleaned_page)
        return {"pages": pages}
    except FileNotFoundError:
        # File not found error
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        # Other exceptions
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse_pdf_sentences/")
async def parse_pdf_sentences():
    # this function will parse an entire pdf to sentences array
    pages = await parse_pdf_pages()
    try:
        sentences = []
        for page in pages.get("pages"):
            sentences.append(re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', page))
        return sentences
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_embeddings/")
async def generate_embeddings():
    # this function will take a batch of sentences and pass it to the embedding endpoint
    try:
        sentences = await parse_pdf_sentences()
        await asyncio.gather(*(make_database_embedding(sentence) for sentence in sentences))
    # write proper exceptions to handle errors here
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_summary/")
async def generate_summary():
    # this function will take a batch of pages and create summaries
    try:
        key_points = []
        pages_dict = await parse_pdf_pages()
        pages = pages_dict.get("pages")
        page_summaries = await asyncio.gather(*(create_summary_json(text=page) for page in pages))
        print(page_summaries)
        for page_summary in page_summaries:
            key_points.extend(json.loads(page_summary).get("key_points"))
        response = await create_summary_json(key_points)
        return response
    # write proper exceptions to handle errors here
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=str(e))


async def make_database_embedding(sentence):
    # this function is only used to insert embedding to the database
    # remember to remove the bearer token in next deps
    headers = {
        'Authorization': f'Bearer {os.environ.get("SUPABASE_KEY")}',
        'Content-Type': 'application/json'
    }
    url = 'https://mokzgwuuykjeipsyzuwe.supabase.co/functions/v1/embed'

    data = {
        'input': sentence,
        'document_id': 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await response.json()


async def generate_embedding_query(text):
    # This function will return an embedding of 384 dimensions
    headers = {
        'Authorization': f'Bearer {os.getenv("SUPABASE_KEY")}',
    }
    url = "https://mokzgwuuykjeipsyzuwe.supabase.co/functions/v1/embed_query"
    data = {'input': text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            # Ensure response is successful
            response.raise_for_status()
            return await response.json()


def execute_query(query, params=None):
    # this is a barebone prostgresql query function
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
