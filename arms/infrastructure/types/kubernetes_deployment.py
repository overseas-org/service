import importlib
import os
import base64
import subprocess
import tempfile
from jinja2 import Template
from utils import Folder, File
from mysql_database import Database
from variables import db_creds
from arms.arm import get_arm
from service_comunications.connectors import get_file_from_connector
from service.service import get_service

class KubernetesDeployment:

    def __init__(self, deployment_id):
        db = Database("Infrastructure", db_creds)
        self.id = deployment_id
        deployment = db.get_object_by_id("KubernetesDeployment", deployment_id)
        self.connector_id = deployment.connector_id
        self.image = deployment.image
        self.namespace = deployment.namespace
        self.port = deployment.port
        self.app = deployment.app
        self.include_autoScale = deployment.include_autoScale
        self.include_service = deployment.include_service
        self.min_replicas = deployment.min_replicas
        self.max_replicas = deployment.max_replicas
        self.include_pv = deployment.include_pv
        self.pv_storage_class = deployment.pv_storage_class
        self.pv_storage_path = deployment.pv_storage_path # not being used
        self.pv_mount_path = deployment.pv_mount_path
        self.storage_amount = deployment.storage_amount

    
    def create_infrastructure(self, service_name, repo_type, repo_id):
        repo = get_arm("repo", repo_type, repo_id)

        yamls_folder = self.get_yamls(service_name)

        infrastructure_folder = Folder("infrastructure")
        infrastructure_folder.add_folder(yamls_folder)

        repo.upload_folder(infrastructure_folder)


    def get_yamls(self, service_name):
        folder = Folder(f"{self.app}-deplyment")
        files = [File("deployment.yaml")]
        if self.include_autoScale == "true":
            files.append(File("hpa.yaml"))
        if self.include_service == "true":
            files.append(File("service.yaml"))
        if self.include_pv == "true":
            files.append(File("pv.yaml"))
            files.append(File("pvc.yaml"))
        folder.files = files
        for file in files:
            with open(f"arms/infrastructure/types/kubernetes/yaml_templates/KubernetesDeployment/{file.name}", "r") as f:
                file.content = f.read()
                if file.name == "pv.yaml":
                    if self.pv_storage_class == "local-path":
                        file.content += f"\n  hostPath:\n    path: \"/data/dbs-local-storage/{self.app.lower().replace("_", "-")}\"\n"
        for file in folder.files:
            template = Template(file.content)
            paremeters = {
                "app": self.app,
                "name": self.app.lower().replace("_", "-"),
                "service_name": service_name.lower(),
                "port": self.port,
                "image": f"{self.image}",
                "deployment_variables": self.get_variables_yaml(),
                "maxReplicas": self.max_replicas,
                "minReplicas": self.min_replicas,
                "pv_storage_class": self.pv_storage_class,
                "storage_amount": self.storage_amount,
                "volume": self.get_volume(),
                "volume_mount": self.get_volume_mount()
                }
            file.content = template.render(paremeters)
        return folder
    
    def get_variables_yaml(self):
        db = Database("Infrastructure", db_creds)
        variables = db.get_list_of_objects("KubernetesDeploymentVarriable", {"KubernetesDeployment": self.id})
        yaml_str = ""
        for var in variables:
            yaml_str += f"\n        - name: {var.name}\n          value: \"{var.value}\""
        return yaml_str
    
    def delete_infrastructure(self):
        name = self.app.lower().replace("_", "-")
        command = "kubectl delete {resource} {name} -n {namespace}".format(resource="{}", name=name, namespace=self.namespace)
        commands = []
        if self.include_autoScale:
            commands.append(command.format("hpa"))
        if self.include_service:
            commands.append(command.format("svc"))
        commands.append(command.format("deployment"))
        kubeconfig = get_file_from_connector(self.connector_id, "kubeconfig")
        # Thread-safe kubeconfig temp file
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".yaml") as temp_kubeconfig:
            kubeconfig_content = base64.b64decode(kubeconfig["file_content"]).decode("utf-8")
            temp_kubeconfig.write(kubeconfig_content)
            temp_kubeconfig_path = temp_kubeconfig.name

        env = os.environ.copy()
        env["KUBECONFIG"] = temp_kubeconfig_path

        try:
            for cmd in commands:
                subprocess.run(cmd, shell=True, env=env)
        finally:
            os.remove(temp_kubeconfig_path)

    def get_volume(self):
        if not self.include_pv == "true":
            return ""
        return f"""volumes:
      - name: {self.app}-volume
        persistentVolumeClaim:
          claimName: {self.app}"""
    
    def get_volume_mount(self):
        if not self.include_pv == "true":
            return ""
        return f"""volumeMounts:
        - mountPath: "{self.pv_mount_path}"
          name: {self.app}-volume"""
    
    def redefine_network_security(self, service_name, service_connections, repo_type, repo_id, service_id):
        allowed_service_accounts = []
        for service_connection in service_connections:
            if service_connection["destination_service_id"] == service_id:
                service_connection_obj = get_service(service_connection["source_service_id"], as_dict=False)
                if service_connection_obj.infrastructure_type == "KubernetesDeployment":
                    # make sure service account exists for the source service or maybe assume it is  
                    # KubernetesDeployment(service_connection_obj.infrastructure_id).add_service_account
                    allowed_service_accounts.append({
                                "namespace": get_arm("infrastructure", service_connection_obj.infrastructure_type, service_connection_obj.infrastructure_id).namespace,
                                "name": service_connection_obj.service_name,
                                "type": "KubernetesDeployment"
                            })
        if allowed_service_accounts:
            file = self.add_istio_authorization_policy(service_name, allowed_service_accounts)
            infrastructure_folder = Folder("infrastructure")
            infrastructure_folder.add_page(file)

            repo = get_arm("repo", repo_type, repo_id)
            repo.upload_folder(infrastructure_folder)
    
    def add_istio_authorization_policy(self, service_name, allowed_service_accounts):
        yaml = ""
        with open(f"arms/infrastructure/types/kubernetes/yaml_templates/KubernetesDeployment/istio_authorization_policy.yaml", "r") as f:
            yaml = f.read()
        template = Template(yaml)
        paremeters = {
            "app": self.app,
            "name": self.app.lower().replace("_", "-"),
            "service_name": service_name.lower(),
            "service_accounts": self.get_service_accounts_istio_authorization_policy(allowed_service_accounts)
        }
        yaml = template.render(paremeters)
        return File("istio_authorization_policy.yaml", yaml)

    def get_service_accounts_istio_authorization_policy(self, allowed_service_accounts):
        service_accounts = ""
        for sa in allowed_service_accounts:
            if sa["type"] == "KubernetesDeployment":
                service_accounts += f"\n        - cluster.local/ns/{sa["namespace"]}/sa/{sa["name"]}"
        return service_accounts
    