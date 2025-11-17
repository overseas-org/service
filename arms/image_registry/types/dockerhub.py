import requests
from mysql_database import Database
from variables import db_creds
from service_comunications.connectors import get_connector
from arms.arm import update_existens
from arms.errors import ArmExists


class Dockerhub:
    def __init__(self, rgistry_id):
        db = Database("ImageRegistry", db_creds)
        registry = db.get_object_by_id("Dockerhub", rgistry_id)
        self.id = registry.id
        self.image = registry.image_name
        self.connector = get_connector(registry.connector_id)
        self.url  = registry.url

    def create_image_registry(self):
        image = self.image.lower()
        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

        # Data for repository creation
        data = {
            "name": image,
            "is_private": False,  # Set to True for a private repo
            "namespace": self.connector["username"],
            "description": "My new Docker repository",
        }

        # Send POST request to create repository
        response = requests.post("https://hub.docker.com/v2/repositories/", json=data, headers=headers)

        # Check response
        if response.status_code == 201:
            print(f"Repository '{image}' created successfully!")
            self.url  = f"https://hub.docker.com/repository/docker/{self.connector["username"]}/{image}/general"
            self.update_url()
            update_existens("ImageRegistry", "Dockerhub", self.id)
        elif response.status_code == 400 and "already exists" in response.text:
            self.url  = f"https://hub.docker.com/repository/docker/{self.connector["username"]}/{image}/general"
            self.update_url()
            update_existens("ImageRegistry", "Dockerhub", self.id, "true")
            raise ArmExists(f"Dockerhub repository {image} already exists")
        else:
            print(f"Failed to create repository: {response.text}")
            update_existens("ImageRegistry", "Dockerhub", self.id, "false")

    def delete_image_registry(self):
        image = self.image.lower()
        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {self.connector["token"]}",
            "Content-Type": "application/json",
        }

        # Send POST request to create repository
        response = requests.delete(f"https://hub.docker.com/v2/repositories/{self.connector["username"]}/{image}/", headers=headers)

        # Check response
        if response.status_code == 202:
            print(f"Repository '{image}' deleted successfully!")
            update_existens("ImageRegistry", "Dockerhub", self.id, "false")
        else:
            print(f"Failed to delete repository: {response.text}")

    
    def get_login_step(self):
        return f"echo $acr_pass | docker login --username $acr_user --password-stdin"

    def update_url(self):
        db = Database("ImageRegistry", db_creds)
        db.update_object("Dockerhub", self.id, {"url": self.url})

    def get_image(self):
        return f"{self.connector["username"]}/{self.image}"
    

    def get_token(self):
        auth_url = "https://hub.docker.com/v2/auth/token"
        body = {
            "identifier": self.connector["username"],
            "secret": self.connector["token"]
        }
        headers = {
            "Content-Type": "application/json"
        }
        resp = requests.post(auth_url, headers=headers, json=body)
        resp.raise_for_status()
        return resp.json()["access_token"]