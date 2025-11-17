import importlib
from utils import capatlize, decapatlize
from arms.arm import create_service_arm, delete_service_arm

def create_repo(repo_info):
    return create_service_arm("repo", repo_info)

def delete_repo(repo_type, repo_id):
    delete_service_arm("repo", repo_type, repo_id)

def add_webhook(repo_type, repo_id, host):
    module = importlib.import_module(f"arms.repo.types.{decapatlize(repo_type)}")
    arm_obj = getattr(module, repo_type)(repo_id)
    arm_obj.add_webhook(f"{host}/github-webhook/")