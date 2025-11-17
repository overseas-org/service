from arms.pipeline.jenkins.objects.Stage import Stage
from arms.pipeline.jenkins.objects.Script import Script
from service_comunications.connectors import get_connector

from arms.pipeline.jenkins.objects.credentials.userCredential import UserCredential
from arms.arm import get_arm

def get_docker_build(image_registry_type, image_registry_id):
    image_registry = get_arm("image_registry", image_registry_type, image_registry_id)
    build = Stage("Build")
    # registry_connctor = get_connector(image_registry.connector_id)
    tag = f"{image_registry.connector['username']}/{image_registry.image.lower()}:1.$BUILD_NUMBER"
    build.credentials.append(UserCredential(image_registry.connector["username"], image_registry.connector["token"], "acr_login"))
    # service.pipeline.install_jenkins_plugin("Docker Pipeline")
    docker_script = Script()
    docker_script.commands.append(f"docker.withRegistry('', 'acr_login') {{\n\t\t\t\t\t\tdef dockerImage = docker.build(\"{tag}\")\n\t\t\t\t\t\tdockerImage.push()\n\t\t\t\t\t}}")
    build.steps.append(docker_script)
    return build