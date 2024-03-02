from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Depends, Request
from celery_app.celery_app import app as celery_app
from models.main import PreprocessBody, GenerateMCQBody, QuizBody

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

    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/ticktock/")
async def tick_tock():
    task = celery_app.send_task("ticktock")

    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post("/quiz/")
async def quiz(
    request: QuizBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)
):
    task = celery_app.send_task(
        "quiz", args=[request.quiz_id, request.default_model, *tokens]
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post("/rapid-quiz/")
async def rapid_quiz(
    request: QuizBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)
):
    task = celery_app.send_task(
        "rapid-quiz", args=[request.quiz_id, request.default_model, *tokens]
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get("/{worker_name}/{task_id}")
async def check_task_status(worker_name: str, task_id: str):
    worker_functions = ["preprocess", "generate_mcq", "ticktock", "quiz", "rapid-quiz"]

    if worker_name not in worker_functions:
        raise HTTPException(status_code=404, detail="Worker not found")

    task = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "task_status": task.state, "task_result": task.info}
