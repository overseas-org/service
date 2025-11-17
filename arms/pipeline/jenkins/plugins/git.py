from arms.pipeline.jenkins.objects.Stage import Stage
from arms.pipeline.jenkins.objects.credentials.userCredential import UserCredential
from service_comunications.connectors import get_connector
from arms.arm import get_arm


def get_git_clone(repo_type, repo_id):
    repo = get_arm("repo", repo_type, repo_id)
    clone = Stage("Clone Repository")
    # repo_connctor = get_connector(repo.connector_id)
    if repo_type == "Github":
        # clone.credentials.append(GithubAppCredential(service.repo.app_id, service.repo.key_path))
        clone.credentials.append(UserCredential(repo.connector["username"], repo.connector["pat"], "github_pat"))
        clone.steps.append(f"git branch: 'main', credentialsId: 'github_app', url: '{repo.url}'")
    return clone