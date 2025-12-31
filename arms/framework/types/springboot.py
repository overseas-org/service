from utils import Folder, File
from arms.arm import get_arm
from arms.endpoints.endpoints import get_service_endpoints
import requests
import zipfile
import io
from mysql_database import Database
from variables import db_creds

class Springboot:
    def __init__(self, framework_id):
        db = Database("Framework", db_creds)
        self.params = db.get_object_by_id("Springboot", framework_id, as_dict=True)

    def create_framework(self, service_id, repo_type, repo_id):
        repo = get_arm("repo", repo_type, repo_id)

        files = self.get_files(service_id)

        repo.upload_files(files)
        
    def get_files(self, service_id):
        # endpoints = get_service_endpoints(service_id)
        files = []
        start_boot_folder = self.generate_start_boot_files("demo")
        files.extend(start_boot_folder.folders)
        files.extend(start_boot_folder.files)
        files.append(self.generate_dockerfile())
        return files

    
    def generate_start_boot_files(self, name):
        url = "https://start.spring.io/starter.zip"
        response = requests.get(url, params=self.params)
        response.raise_for_status()

        zip_bytes = io.BytesIO(response.content)

        folder = Folder(name)
        with zipfile.ZipFile(zip_bytes) as z:
            for file_name in z.namelist():
                content = z.read(file_name).decode("utf-8")
                page = File(file_name, content)
                folder.add_page(page)
        return folder


    def generate_dockerfile(self):
        dockerfile = File("dockerfile")
        dockerfile.content = """# =========================
# Build stage (Java 25)
# =========================
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app

# Install Maven manually
RUN apt-get update && \
    apt-get install -y maven && \
    rm -rf /var/lib/apt/lists/*

COPY pom.xml .
RUN mvn -B dependency:go-offline

COPY src ./src
RUN mvn clean package -DskipTests

# =========================
# Runtime stage (Java 25)
# =========================
FROM eclipse-temurin:25-jre
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java","-jar","app.jar"]

"""
        return dockerfile
    

