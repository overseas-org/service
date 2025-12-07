import requests
from logger import logger
from service_comunications.microservices import progress


def create_task(data):
    response = requests.post(f"{progress}/task", headers={'Content-Type': 'application/json'}, json=data)
    if response.status_code == 200:
        return response.json()["task_id"]
    else:
        logger.error(response.text)

def start_task(task_id):
    response = requests.post(f"{progress}/start_task?task_id={task_id}")
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(response.text)

def get_task(task_id):
    response = requests.get(f"{progress}/task?task_id={task_id}")
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(response.text)

def finish_step(task_id, step_name, succeess=True):
    response = requests.post(f"{progress}/finish_step?task_id={task_id}", headers={'Content-Type': 'application/json'}, json={
        "step_name": step_name,
        "success": "true" if succeess else "false"
    })
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(response.text)

def start_step(task_id, step_name):
    response = requests.post(f"{progress}/start_step?task_id={task_id}", headers={'Content-Type': 'application/json'}, json={
        "step_name": step_name
    })
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(response.text)


