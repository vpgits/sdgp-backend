from concurrent.futures import Future
import json
import celery
import requests
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def parse_runpod_response(response: dict) -> str:
    try:
        llm_response_status = response.get("status")
        if llm_response_status is not None:
            if llm_response_status == "FAILED":
                raise Exception("Runpod request failed")
        llm_response = response.get("output")
        if llm_response is not None and llm_response_status is not None:
            special_token = "### Output :"
            output_start = llm_response.find(special_token) + len(special_token)
            if output_start > len(special_token):
                json_str = llm_response[output_start:].strip()
                output_json = json.loads(json_str)
                mcq = output_json.get("Output")
                return mcq
        else:
            logging.error("Runpod response is None")
    except Exception as e:
        logging.error(f"Error parsing runpod response: {e}")
        raise e

    # special_token = "### Output :"
    # output_start = llm_response.find(special_token) + len(special_token)
    # if output_start > len(special_token):
    #     json_str = llm_response[output_start:].strip()
    #     output_json = json.loads(json_str)
    #     mcq = output_json.get("Output")
    #     return mcq
