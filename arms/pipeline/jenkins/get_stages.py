from arms.pipeline.jenkins.plugins.docker import get_docker_build
from arms.pipeline.jenkins.plugins.kubernetes import get_kubernetes_deploy
from arms.pipeline.jenkins.plugins.git import get_git_clone

from arms.pipeline.jenkins.objects.Stage import Stage


def get_clone(repo_type, repo_id):
    clone = get_git_clone(repo_type, repo_id)
    return clone; 

def get_build(build_type, image_registry_type, image_registry_id):
    build = Stage("Build")
    match build_type:
        case "docker":
            build = get_docker_build(image_registry_type, image_registry_id)
    return build

def get_test(test_type):
    test = Stage("test")
    match test_type:
        case "pytest":
            test.steps.append("bat 'pip install -r requirements.txt'")
            test.steps.append("bat 'pytest --junitxml=report.xml'")
    return test; 


def get_deploy(infrastructure_type, infrastructure_id):
    deploy = Stage("Deploy")
    if "Kubernetes" in infrastructure_type:
        deploy = get_kubernetes_deploy(infrastructure_type, infrastructure_id)
    return deploy




