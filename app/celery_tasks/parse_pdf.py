import asyncio
import os
import time

from app.api.create_embeddings import sentence_embeddings
from celery_worker.celery_app import app
from app.api.parse_pdf import parse_pdf_pages, parse_pdf_sentences, sliding_window
from app.api.create_summary import create_summary_json


@app.task(name="parse_pdf")
def parse_pdf_worker(path, document_id, user_id):
    # this function will parse an entire pdf into an array of pages, then push to database
    try:
        pages = parse_pdf_pages(path)
        chunks = sliding_window(pages.get("pages"))
        pages = ''.join(pages.get("pages"))
        loop = asyncio.get_event_loop()
        response1, response2 = loop.run_until_complete(create_embeddings_and_summary(chunks[:1], pages[:256],
                                                                                     document_id, user_id))
        if response1 & response2:
            return {"message": "success"}
        else:
            return {"message": "failed"}
    except Exception as e:
        # Other exceptions
        print(str(e))
        return {"message": f"failed: {str(e)}"}
    # finally:
    #     os.remove(f'./resources/{path}')


@app.task(name='tick-tock')
def tick_tock_worker():
    time.sleep(5)
    print('tick-tock')
    return 'tick-tock'


async def create_embeddings_and_summary(chunks, pages, document_id, user_id):
    task1 = asyncio.create_task(sentence_embeddings(chunks, document_id))
    task2 = asyncio.create_task(
        create_summary_json(pages, document_id, user_id, subtext="Output maximum 10 key points"))
    response1, response2 = await asyncio.gather(task1, task2)
    return response1, response2
