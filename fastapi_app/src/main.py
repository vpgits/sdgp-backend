from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Depends, Request
from celery_app.celery_app import app as celery_app
from models.main import PreprocessBody, QuizBody

app = FastAPI()


def extract_header_auth_tokens(request: Request) -> tuple[str, str]:
    """
    Extract the access token and refresh token from the request headers.
    Supabase's auth token and refresh token are used for authentication.
    Useful in Row Level Access control using the database, without using the override token.
    """
    access_token = request.headers.get("authorization")
    refresh_token = request.headers.get("refresh-token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    return access_token, refresh_token


@app.post(
    "/preprocess/",
    description="Endpoint to preprocess the document",
    responses={
        200: {
            "task_id": "task_id",
            "message": "Task has been sent to the background worker",
        }
    },
)
async def preprocess(
    request: PreprocessBody,
    tokens: tuple[str, str] = Depends(extract_header_auth_tokens),
):
    """
    Submit a preprocess task to the background worker.
     - **request**: The request body containing the document ID
    - **tokens**: A tuple of authentication tokens extracted from the request headers. Related to supabase's auth token and refresh token

    Returns:
    - **200 OK** with JSON object containing the task ID and a success message.
    """
    task = celery_app.send_task(
        "preprocess", args=[request.path, request.document_id, *tokens]
    )

    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get(
    "/ticktock/",
    description="A simple endpoint to test the background worker.",
    responses={
        200: {
            "task_id": "task_id",
            "message": "Task has been sent to the background worker",
        }
    },
)
async def tick_tock():
    """
    A simple endpoint to test the background worker."""
    task = celery_app.send_task("ticktock")

    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post(
    "/quiz/",
    description="Endpoint to generate the quiz",
    responses={
        200: {
            "task_id": "task_id",
            "message": "Task has been sent to the background worker",
        }
    },
)
async def quiz(
    request: QuizBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)
):
    """
    Submit a quiz task to the background worker.
    - **request**: The request body containing the quiz ID
    - **tokens**: A tuple of authentication tokens extracted from the request headers. Related to supabase's auth token and refresh token

    Returns:
    - **200 OK** with JSON object containing the task ID and a success message.
    """
    task = celery_app.send_task(
        "quiz", args=[request.quiz_id, request.default_model, *tokens]
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.post(
    "/rapid-quiz/",
    description="Endpoint to generate the rapid quiz",
    responses={
        200: {
            "task_id": "task_id",
            "message": "Task has been sent to the background worker",
        }
    },
)
async def rapid_quiz(
    request: QuizBody, tokens: tuple[str, str] = Depends(extract_header_auth_tokens)
):
    """
     Submit a rapid quiz task to the background worker.

    - **request**: The request body containing the quiz ID.
    - **tokens**: A tuple of authentication tokens extracted from the request headers. Related to supabase's auth token and refresh token

    Returns:
    - **200 OK** with JSON object containing the task ID and a success message.
    """
    task = celery_app.send_task(
        "rapid-quiz", args=[request.quiz_id, request.default_model, *tokens]
    )
    return {
        "task_id": task.id,
        "message": "Task has been sent to the background worker",
    }


@app.get(
    "/{worker_name}/{task_id}",
    description="Check the status of a task",
    responses={
        200: {'"task_id": task_id, "task_status": task.state, "task_result": task.info'}
    },
)
async def check_task_status(worker_name: str, task_id: str):
    """
    Check the status of a task.

    Args:
        worker_name (str): The name of the worker function.
        task_id (str): The ID of the task.

    Returns:
        **200 OK** with dict: A dictionary containing the task ID, task status, and task result.
    """
    worker_functions = ["preprocess", "generate_mcq", "ticktock", "quiz", "rapid-quiz"]

    if worker_name not in worker_functions:
        raise HTTPException(status_code=404, detail="Worker not found")

    task = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "task_status": task.state, "task_result": task.info}
