

from arms.arm import create_service_arm, delete_service_arm
from arms.arm import get_arm

def create_pipeline(repo_info, **args):
    return create_service_arm("pipeline", repo_info, **args)

def trigger_pipeline(pipeline_type, pipeline_id):
    get_arm("pipeline", pipeline_type, pipeline_id).trigger_pipeline()

def get_pipeline_host(pipeline_type, pipeline_id):
    return get_arm("pipeline", pipeline_type, pipeline_id).host

def delete_pipeline(pipeline_type, pipeline_id):
    delete_service_arm("pipeline", pipeline_type, pipeline_id)