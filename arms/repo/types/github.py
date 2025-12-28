from logger import logger
import requests
import base64
import time
import jwt

from mysql_database import Database
from variables import db_creds
from service_comunications.connectors import get_connector
from arms.arm import update_existens
from arms.errors import ArmExists


class Github:

    def __init__(self, repo_id):
        db = Database("Repo", db_creds)
        repo = db.get_object_by_id("Github", repo_id)
        self.connector = get_connector(repo.connector_id)
        self.id = repo.id
        self.name = repo.name
        self.address = f"{self.connector['organization']}/{self.name}" if self.connector["organization"] else f"{self.connector['account']}/{self.name}"
        self.url = repo.url
        self.token = self.connector["pat"]

    def delete_repo(self):
        repo_url = f"https://api.github.com/repos/{self.address}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.delete(
            repo_url,
            headers=headers
            # auth=(self.connector["username"], self.token)
        )
        if response.status_code == 204:
            logger.info(f"successfully deleted github repository '{self.name}'")
            update_existens("Repo", "Github", self.id, "false")
        else:
            logger.info("Error:", response.json())


    def create_repo(self, description="", private=False):
        if self.connector["organization"]:
            repo_url = f"https://api.github.com/orgs/{self.connector['organization']}/repos"
        else:
            repo_url = "https://api.github.com/user/repos"
        repo_data = {
            "name": self.name,
            "description": description,
            "private": private
            }
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.post(
            repo_url,
            json=repo_data,
            headers=headers
            # auth=(self.connector["username"], self.token)
        )
        if response.status_code in [201]:
            self.update_url(response.json()["html_url"])
        elif response.status_code == 422:
            update_existens("Repo", "Github", self.id, "true")
            response = self.get_repo()
            self.update_url(response["html_url"])
            raise ArmExists("Repository already exists on this account")
        else:
            update_existens("Repo", "Github", self.id, "false")
            logger.error(f"error while creaing repo {response.json()}")
            raise Exception(f"error while creaing repo {response.json()}")
        return response
    
    def get_repo(self):
        repo_url = f"https://api.github.com/repos/{self.address}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(
            repo_url,
            headers=headers
            # auth=(self.connector["username"], self.token)
        )
        if response.status_code in [200]:
            return response.json()
        else:
            raise Exception("Failed to fetch Repository")
    
    def get_token(self):
        with open(self.key_path, 'rb') as pem_file:
            signing_key = pem_file.read()

        payload = {
            # Issued at time
            'iat': int(time.time()),
            # JWT expiration time (10 minutes maximum)
            'exp': int(time.time()) + 600,
            
            # GitHub App's client ID
            'iss': self.client_id
        }

        # Create JWT
        encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')
        headers = {
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # installation id is a variable - dont hard code
        url = f"https://api.github.com/app/installations/61977373/access_tokens"
        response = requests.post(url, headers=headers)

        if response.status_code == 201:
            return response.json()["token"]
        else:
            raise Exception(f"Failed to get token: {response.json()}")
        
    def upload_files(self, files):
        for file in files:
            if file:
                self.upload_file(file.name, file.content)

    
    def upload_file(self, file_path, content, commit_message="Add file via API"):
        """Uploads a single file to GitHub via API."""
        if self.connector["organization"]:
            url = f"https://api.github.com/repos/{self.connector['organization']}/{self.name}/contents/{file_path}"
        else:
            url = f"https://api.github.com/repos/{self.connector['account']}/{self.name}/contents/{file_path}"
        
        # Encode content to Base64 (required by GitHub API)
        encoded_content = base64.b64encode(content.encode()).decode()
        
        # Check if file already exists (GitHub requires SHA for updates)
        response = requests.get(url, headers={"Authorization": f"token {self.token}"})
        sha = response.json().get("sha") if response.status_code == 200 else None

        data = {
            "message": commit_message,
            "content": encoded_content,
            "sha": sha  # Required if updating an existing file
        }

        headers = {"Authorization": f"token {self.token}"}
        response = requests.put(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            logger.info(f"Uploaded {file_path}")
        else:
            logger.info(f"Error uploading {file_path}: {response.text}")

    def delete_file(self, file_path, commit_message="Delete file via API"):
        """Deletes a single file to GitHub via API."""
        if self.connector["organization"]:
            url = f"https://api.github.com/repos/{self.connector['organization']}/{self.name}/contents/{file_path}"
        else:
            url = f"https://api.github.com/repos/{self.connector['account']}/{self.name}/contents/{file_path}"
        
        
        # Check if file already exists (GitHub requires SHA for updates)
        response = requests.get(url, headers={"Authorization": f"token {self.token}"})
        sha = response.json().get("sha") if response.status_code == 200 else None

        data = {
            "message": commit_message,
            "sha": sha  # Required if updating an existing file
        }

        headers = {"Authorization": f"token {self.token}"}
        response = requests.delete(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            logger.info(f"Deleated {file_path}")
        else:
            logger.info(f"Error deleting {file_path}: {response.text}")

    def upload_folder(self, folder, parent_path=""):
        """Recursively uploads folder and its files to GitHub."""
        if parent_path == "":
            parent_path = folder.name
        for file in folder.files:
            file_path = f"{parent_path}/{file.name}".strip("/")
            self.upload_file(file_path, file.content)

        for subfolder in folder.folders:
            self.upload_folder(subfolder, f"{parent_path}/{subfolder.name}")


    def add_webhook(self, host, ssl_disable=False):
        """Adds a webhook to the repository."""
        url = f"https://api.github.com/repos/{self.address}/hooks"
        
        data = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": host,
                "content_type": "json",
                "insecure_ssl": "1" if ssl_disable else "0"
            }
        }
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info("Webhook added successfully!")
            return response.json()
        else:
            logger.info(f"Failed to add webhook: {response.text}")
            return None


    def update_url(self, url):
        self.url = url
        update_existens("Repo", "Github", self.id)
        db = Database("Repo", db_creds)
        db.update_object("Github", self.id, {"url": url})
