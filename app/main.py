import uvicorn
from fastapi import FastAPI
from app.api.custom_classes import Document
from app.celery_tasks.parse_pdf import parse_pdf_worker, tick_tock_worker

app = FastAPI()


@app.post("/preprocess/")
async def preprocess(props: Document):
    task = parse_pdf_worker.delay(props.path, props.document_id, props.user_id)
    return {"task_id": task.id, "message": "Task has been sent to the background worker"}


@app.get("/preprocess/{task_id}")
async def status_preprocess(task_id: str):
    task = parse_pdf_worker.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "task_status": task.status,
        "task_result": task.result
    }


@app.get("/ticktock/")
async def tick_tock():
    task = tick_tock_worker.delay()
    return {"task_id": task.id, "message": "Task has been sent to the background worker"}


@app.get("/ticktock/{task_id}")
async def check_task_status(task_id: str):
    task = tick_tock_worker.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "task_status": task.status,
        "task_result": task.result
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
