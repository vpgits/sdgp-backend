from fastapi import FastAPI, HTTPException, Depends, Request
from app.models.main import PreprocessBody, GenerateMCQBody
from app.celery_tasks.generate_mcq import generate_mcq_worker
from app.celery_tasks.preprocess import preprocess_worker
from app.celery_tasks.tick_tock import tick_tock_worker


app = FastAPI()


def extract_header_auth_tokens(request: Request) -> tuple[str, str]:
    access_token = request.headers.get("authorization")
    refresh_token = request.headers.get("refresh-token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    return access_token, refresh_token


@app.post("/preprocess/")
async def preprocess(request: PreprocessBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)):
    task = preprocess_worker.delay(
        request.path, request.document_id, *tokens
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post("/generate_mcq/")
async def generate_mcq(request: GenerateMCQBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)):
    task = generate_mcq_worker.delay(
        request.document_id, request.key_point_id, *tokens
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/ticktock/")
async def tick_tock():
    task = tick_tock_worker.delay()
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/{worker_name}/{task_id}")
async def check_task_status(worker_name: str, task_id: str):
    worker_function = {
        'preprocess': preprocess_worker,
        'generate_mcq': generate_mcq_worker,
        'ticktock': tick_tock_worker
    }.get(worker_name)

    if not worker_function:
        raise HTTPException(status_code=404, detail="Worker not found")
    task = worker_function.AsyncResult(task_id)
    return {"task_id": task_id, "task_status": task.status, "task_result": task.result}
