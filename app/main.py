import json
import logging

import uvicorn
from fastapi import FastAPI, Request, HTTPException

# from app.api.custom_classes import Document, Mcq
from app.celery_tasks.parse_pdf import (
    parse_pdf_worker,
    tick_tock_worker,
    generate_mcq_worker,
)

app = FastAPI()


@app.post("/preprocess/")
async def preprocess(request: Request):
    access_token = request.headers.get("authorization")
    refresh_token = request.headers.get("refresh-token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    path = body.get("path")
    document_id = body.get("document_id")
    user_id = body.get("user_id")
    task = parse_pdf_worker.delay(
        path, document_id, user_id, access_token, refresh_token
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/preprocess/{task_id}")
async def status_preprocess(task_id: str):
    task = parse_pdf_worker.AsyncResult(task_id)
    return {"task_id": task_id, "task_status": task.status, "task_result": task.result}


@app.get("/ticktock/")
async def tick_tock():
    task = tick_tock_worker.delay()
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/ticktock/{task_id}")
async def check_task_status(task_id: str):
    task = tick_tock_worker.AsyncResult(task_id)
    return {"task_id": task_id, "task_status": task.status, "task_result": task.result}


@app.post("/generate_mcq/")
async def generate_mcq(request: Request):
    access_token = request.headers.get("authorization")
    refresh_token = request.headers.get("refresh-token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    document_id = body.get("document_id")
    key_point_id = body.get("key_point_id")
    user_id = body.get("user_id")
    task = generate_mcq_worker.delay(
        document_id, key_point_id, user_id, access_token, refresh_token
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/generate_mcq/{task_id}")
async def check_task_status(task_id: str):
    task = generate_mcq_worker.AsyncResult(task_id)
    return {"task_id": task_id, "task_status": task.status, "task_result": task.result}
