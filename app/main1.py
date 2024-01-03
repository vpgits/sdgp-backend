import asyncio
import json
import re
from io import BytesIO
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.api.create_embeddings import make_database_embedding, generate_embedding_query
from app.api.create_summary import create_summary_json
from app.api.custom_classes import Document, Embeddings, Query
from app.api.database import download_file

app = FastAPI()
load_dotenv()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/parse_pdf_pages/")
async def parse_pdf_pages(props: Document):
    # this function will parse an entire pdf into an array of pages
    try:
        download_file(props.path)
        with open(f'./resources/{props.path}', 'rb') as f:
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
async def parse_pdf_sentences(pages: list):
    # this function will parse an entire pdf to sentences array

    try:
        sentences = []
        for page in pages:
            sentences.extend(re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', page))
        return sentences
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_embeddings/")
async def generate_embeddings(props: Embeddings):
    # this function will take a batch of sentences and create embeddings
    responses = []
    try:
        sentences = await parse_pdf_sentences(props.pages)
        responses = await asyncio.gather(
            *(make_database_embedding(sentence, props.document_id) for sentence in sentences[:1]))
        if all(response["message"] == "Embedding added successfully!" for response in responses):
            return {"message": "Embeddings added successfully!"}
        else:
            return {"message": "Embeddings not added successfully!"}
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=responses)


@app.post("/generate_embedding/")
async def generate_embedding(props: Query):
    try:
        response = await generate_embedding_query(props.query)
    except Exception as e:
        # Raise a HTTPException with status code 500
        raise HTTPException(status_code=500, detail=str(e))
    return response


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
