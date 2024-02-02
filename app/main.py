from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Depends, Request
from celery_worker.celery_app import app as celery_app
from app.models.main import PreprocessBody, GenerateMCQBody, QuizBody

# from app.celery_tasks.generate_mcq import generate_mcq_worker
# from app.celery_tasks.preprocess import preprocess_worker
# from app.celery_tasks.tick_tock import tick_tock_worker
# from app.celery_tasks.quiz import quiz_worker


app = FastAPI()


def extract_header_auth_tokens(request: Request) -> tuple[str, str]:
    access_token = request.headers.get("authorization")
    refresh_token = request.headers.get("refresh-token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    return access_token, refresh_token


@app.post("/preprocess/")
async def preprocess(
    request: PreprocessBody,
    tokens: tuple[str, str] = Depends(extract_header_auth_tokens),
):
    task = celery_app.send_task(
        "preprocess", args=[request.path, request.document_id, *tokens]
    )
    # task = preprocess_worker.delay(request.path, request.document_id, *tokens)
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post("/generate_mcq/")
async def generate_mcq(
    request: GenerateMCQBody,
    tokens: tuple[str, str] = Depends(extract_header_auth_tokens),
):
    task = celery_app.send_task(
        "generate_mcq", args=[request.question_id, request.key_point_id, *tokens]
    )
    # task = generate_mcq_worker.delay(request.question_id, request.key_point_id, *tokens)
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/ticktock/")
async def tick_tock():
    task = celery_app.send_task("ticktock")
    # task = tick_tock_worker.delay()
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post("/quiz/")
async def quiz(
    request: QuizBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)
):
    task = celery_app.send_task("quiz", args=[request.quiz_id, *tokens])
    # task = quiz_worker.delay(request.quiz_id, **tokens)
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/{worker_name}/{task_id}")
async def check_task_status(worker_name: str, task_id: str):
    worker_functions = ["preprocess", "generate_mcq", "ticktock", "quiz"]

    if worker_name not in worker_functions:
        raise HTTPException(status_code=404, detail="Worker not found")

    task = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "task_status": task.status,
        "task_result": task.result if task.ready() else None,
    }
