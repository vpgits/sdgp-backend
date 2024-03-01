import json
import celery
import requests
import os


def check_endpoint_health():
    url = f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_WORKER_ID')}/health"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.getenv("RUNPOD_API_KEY"),
    }
    response = requests.request("GET", url, headers=headers)
    if response.status_code == 200:
        workers = response.json().get("workers")
        if workers.get("ready") > 0 or workers.get("running") > 0:
            return True
        elif (
            workers.get("throttled") - workers.get("ready") + workers.get("running") > 0
        ):
            return False
    return False


def cancel_runpod_request(request_id: str):
    url = (
        f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_WORKER_ID')}/cancel/{request_id}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.getenv("RUNPOD_API_KEY"),
    }
    response = requests.request("GET", url, headers=headers)
    return response.json()


def update_task_state(task: celery.Task, message: str, state="PROGRESS"):
    task.update_state(state=state, meta={"status": message})


def parse_runpod_response(llm_response: str) -> str:
    special_token = "### Output :"
    output_start = llm_response.find(special_token) + len(special_token)
    if output_start > len(special_token):
        json_str = llm_response[output_start:].strip()
        output_json = json.loads(json_str)
        mcq = output_json.get("Output")
        return mcq
