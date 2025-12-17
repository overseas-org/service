from logger import logger
import requests
import json
import base64
from arms.pipeline.jenkins.get_stages import get_build, get_deploy, get_test, get_clone
from arms.pipeline.jenkins.objects.credentials.SecretFile import SecretFile
from service_comunications.connectors import get_connector
from mysql_database import Database
from variables import db_creds
from logger import logger
from service.get_service import get_container_service
from arms.arm import get_arm
#redo

class Jenkins:
    def __init__(self, pipeline_id):
        db = Database("Pipeline", db_creds)
        pipeline = db.get_object_by_id("Jenkins", pipeline_id)
        self.id = pipeline_id
        self.connector = get_connector(pipeline.connector_id)
        self.name = pipeline.name
        self.folder = pipeline.folder
        self.host = self.connector['host']
        folder = f"/{self.folder}".replace("/", "/job/") if self.folder else ""
        self.url = f"{self.connector['host']}{folder}/job/{self.name}"

    
    def to_groovy(self, pipeline):
        groovy_str = "pipeline {\n\tagent any\n\tstages {"
        for stage in pipeline["stages"]:
            groovy_str += stage.to_groovy()
        groovy_str += "\n\t}\n}"
        return groovy_str
    
    def get_properties(self, repo_type, repo_id):
        repo = get_arm("repo", repo_type, repo_id)
        properties = ""
        if repo_type == "Github":
            properties += f"""<com.coravy.hudson.plugins.github.GithubProjectProperty plugin="github@1.42.0">
                            <projectUrl>{repo.url}.git/</projectUrl>
                            <displayName>{repo.name}</displayName>
                            </com.coravy.hudson.plugins.github.GithubProjectProperty>"""
            properties += self.get_triggers(repo_type)
        return properties
    
    def get_triggers(self, repo_type):
        trigers = ""
        if repo_type == "Github":
            trigers += """
                    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
                    <triggers>
                        <com.cloudbees.jenkins.GitHubPushTrigger plugin="github@1.42.0">
                        <spec></spec>
                        </com.cloudbees.jenkins.GitHubPushTrigger>
                    </triggers>
                    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>""" 
        return trigers

    def create_pipeline_job(self, pipeline_name, groovy_pipeline, properties):
        pipeline_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
                        <flow-definition plugin="workflow-job">
                            <description>My Jenkins Pipeline</description>
                            <properties>{properties}</properties>
                            <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
                                <script>{groovy_pipeline}</script>
                                <sandbox>true</sandbox>
                            </definition>
                        </flow-definition>"""

        # Convert to JSON string
        payload = pipeline_xml

        # Jenkins API URL for creating a job ----------> changing
        folder = f"/{self.folder}".replace("/", "/job/")
        create_url = f"{self.connector['host']}/{folder}/createItem?name={pipeline_name}"

        # Authentication
        auth = (self.connector["username"], self.connector["token"])

        # Headers
        headers = {
            "Content-Type": "application/xml"
        }

        # Get Jenkins crumb for CSRF protection
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.info("failed")

        # Send request to create the pipeline job
        response = requests.post(create_url, headers=headers, data=payload, auth=auth)

        # Output response
        if response.status_code == 200:
            logger.info(f"Pipeline '{pipeline_name}' created successfully!")
        else:
            raise Exception(f"Failed to create pipeline: {response.status_code}, {response.text}")
    
    def create_pipeline(self, service_id):
        service = get_container_service(service_id)
        self.create_folder(self.folder)
        jenkins_pipeline = {
                "agent": "any",
                "stages": []
            }
        stages = jenkins_pipeline["stages"]
        stages.append(get_clone(service.repo_type, service.repo_id))
        stages.append(get_build(service.image_type, service.image_registry_type, service.image_registry_id))
        # stages.append(get_test(service.test_type))
        stages.append(get_deploy(service.infrastructure_type, service.infrastructure_id))
        self.create_credentials(jenkins_pipeline)
        self.create_pipeline_job(service.service_name, self.to_groovy(jenkins_pipeline), self.get_properties(service.repo_type, service.repo_id))
        self.update_url()

    def create_credentials(self, pipeline):
        for stage in pipeline["stages"]:
            for credential in stage.credentials:
                match credential.__class__.__name__:
                    case "SecretFile":
                        self.create_secret_file(credential, folder=self.folder)
                    case "GithubAppCredential":
                        self.create_github_app_cred(credential, folder=self.folder)
                    case "UserCredential":
                        self.create_user_cred(credential, folder=self.folder)


    def create_folder(self, folder_name):
        logger.info("creating folder")
        url = f"{self.connector['host']}/view/all/createItem"


        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        auth = (self.connector["username"], self.connector["token"])
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.error("failed to create folder")
        data = {
            "name": folder_name,
            "mode": "com.cloudbees.hudson.plugins.folder.Folder",
        }
        
        response = requests.post(url, headers=headers, data=data, auth=auth)

        logger.info(response.status_code)


    def install_jenkins_plugin(self, plugin_name):

        plugin_url = f"{self.connector['host']}/pluginManager/installNecessaryPlugins"
        headers = {"Content-Type": "text/xml"}
        xml_data = f"""<jenkins><install plugin="{plugin_name}@latest"/></jenkins>"""

        response = requests.post(plugin_url, auth=(self.connector["username"], self.connector["token"]), 
                                headers=headers, data=xml_data)

        if response.status_code == 200:
            logger.info(f"✅ Plugin '{plugin_name}' is being installed. Restart Jenkins if required.")
        else:
            logger.info(f"❌ Failed to install plugin '{plugin_name}': {response.text}")




    def create_user_cred(self, credential, folder):
        url = f"{self.connector['host']}/job/{folder}/credentials/store/folder/domain/_/createCredentials"


        pipeline_xml = f"""<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl plugin="credentials@1408.va_622a_b_f5b_1b_1">
                            <id>{credential.id}</id>
                            <description></description>
                            <username>{credential.username}</username>
                            <password>{credential.password}</password>
                            <usernameSecret>false</usernameSecret>
                            </com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>"""

        # Convert to JSON string
        payload = pipeline_xml



        # Authentication
        auth = (self.connector["username"], self.connector["token"])

        # Headers
        headers = {
            "Content-Type": "application/xml"
        }

        # Get Jenkins crumb for CSRF protection
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.info("failed")

        # Send request to create the pipeline job
        response = requests.post(url, headers=headers, data=payload, auth=auth)

        # Output response
        if response.status_code == 200:
            logger.info(f"user creds created successfully!")
        else:
            logger.info(f"Failed to create user creds: {response.status_code}, {response.text}")

        logger.info(response.status_code)
        logger.info(response.text)

    def create_secret_text_cred(self, credential, folder=""):
        pass

    # need to test
    def create_github_app_cred(self, credential, folder=""):
        if folder:
            folder = f"/{folder}"
        folder = folder.replace("/", "/job/")
        url = f"{self.connector['host']}{folder}/credentials/store/folder/domain/_/createCredentials"


        pipeline_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
                        <org.jenkinsci.plugins.github__branch__source.GitHubAppCredentials plugin="github-branch-source@1810.v913311241fa_9">
                        <id>github_app</id>
                        <description></description>
                        <appID>1156901</appID>
                        <privateKey>{open(credential.key_path, "rb").read()}</privateKey>
                        <apiUri></apiUri>
                        </org.jenkinsci.plugins.github__branch__source.GitHubAppCredentials>"""

        # Convert to JSON string
        payload = pipeline_xml



        # Authentication
        auth = (self.connector["username"], self.connector["token"])

        # Headers
        headers = {
            "Content-Type": "application/xml"
        }

        # Get Jenkins crumb for CSRF protection
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.info("failed")

        # Send request to create the pipeline job
        response = requests.post(url, headers=headers, data=payload, auth=auth)

        # Output response
        if response.status_code == 200:
            logger.info(f"github app credentials created successfully!")
        else:
            logger.info(f"Failed to create github app credentials: {response.status_code}, {response.text}")

        logger.info(response.status_code)
        logger.info(response.text)

    def create_secret_file(self, credential, folder=""):
        if folder:
            folder = f"/{folder}"
        folder = folder.replace("/", "/job/")
        url = f"{self.connector['host']}/{folder}/credentials/store/folder/domain/_/createCredentials"


        pipeline_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
                        <org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl plugin="plain-credentials@1.4">
                        <scope>GLOBAL</scope>
                        <id>{credential.id}</id>
                        <description>{credential.description}</description>
                        <fileName>{credential.file.name}</fileName>
                        <secretBytes>{credential.file.content}</secretBytes>
                        </org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl>"""

        # Convert to JSON string
        payload = pipeline_xml



        # Authentication
        auth = (self.connector["username"], self.connector["token"])

        # Headers
        headers = {
            "Content-Type": "application/xml"
        }

        # Get Jenkins crumb for CSRF protection
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()['crumb']
        else:
            logger.info("failed")

        # Send request to create the pipeline job
        response = requests.post(url, headers=headers, data=payload, auth=auth)

        # Output response
        if response.status_code == 200:
            logger.info(f"secret file '{credential.file.name}' created successfully!")
        else:
            logger.info(f"Failed to create secret file '{credential.file.name}': {response.status_code}, {response.text}")

        logger.info(response.status_code)
        logger.info(response.text)

    def trigger_pipeline(self):
        folder = f"/{self.folder}".replace("/", "/job/")
        url =  f"{self.connector['host']}{folder}/job/{self.name}/build"


        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        auth = (self.connector["username"], self.connector["token"])
        crumb_response = requests.get(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.info("failed")
        
        response = requests.post(url, headers=headers, auth=auth)

        logger.info(response.status_code)



    def delete_pipeline(self):
        folder = f"/{self.folder}".replace("/", "/job/")
        delete_url = f"{self.connector['host']}/{folder}/job/{self.name}/doDelete"

        # Authentication
        auth = (self.connector["username"], self.connector["token"])

        # Headers
        headers = {
            "Content-Type": "application/xml"
        }

        # Get Jenkins crumb for CSRF protection
        crumb_response = requests.post(f"{self.connector['host']}/crumbIssuer/api/json", auth=auth)
        if crumb_response.status_code == 200:
            headers["Jenkins-Crumb"] = crumb_response.json()["crumb"]
        else:
            logger.info("failed")

        # Send request to create the pipeline job
        response = requests.post(delete_url, headers=headers, auth=auth)

        # Output response
        if response.status_code == 200:
            logger.info(f"Pipeline '{self.name}' deleted successfully!")
        else:
            logger.info(f"Failed to delete pipeline: {response.status_code}, {response.text}")
    
    def update_url(self):
        db = Database("Pipeline", db_creds)
        db.update_object("Jenkins", self.id, {"url": self.url})
