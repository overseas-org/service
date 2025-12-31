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
        endpoints = get_service_endpoints(service_id)
        files = []
        if endpoints and "web" not in [v.strip() for v in self.params["dependencies"].split(",")]:
            self.params["dependencies"] += ", web" if self.params["dependencies"] else "web"
            self.update_db()
        start_boot_folder = self.generate_start_boot_files()
        files.extend(start_boot_folder.folders)
        files.extend(start_boot_folder.files)
        if endpoints:
            files.append(self.generate_rest_controller(endpoints))
        files.append(self.generate_dockerfile())
        return files

    
    def generate_start_boot_files(self):
        url = "https://start.spring.io/starter.zip"
        response = requests.get(url, params=self.params)
        response.raise_for_status()

        zip_bytes = io.BytesIO(response.content)

        folder = Folder(self.params["name"])
        with zipfile.ZipFile(zip_bytes) as z:
            for file_name in z.namelist():
                content = z.read(file_name).decode("utf-8")
                page = File(file_name, content)
                folder.add_page(page)
        return folder
    
    def generate_rest_controller(self, endpoints):
        controller_file = File(f"src/main/java/{"/".join(self.params["groupId"].split("."))}/{self.get_artifact()}/HomeController.java")
        controller_file.content = f"""package {self.params["groupId"]}.{self.get_artifact()};

import java.util.HashMap;
import java.util.Map;

{self.get_rest_mappings_imports(endpoints)}
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {{
    
{self.get_rest_endpoint(endpoints)}
    
}}"""
        return controller_file
        
    def get_rest_mappings_imports(self, endpoints):
        imports_code = ""
        used_methods = [endpoint["method"] for endpoint in endpoints]
        for method in ["GET", "POST", "PUT", "UPDATE", "DELETE"]:
            if method in used_methods:
                imports_code += f"\nimport org.springframework.web.bind.annotation.{method.title()}Mapping;"
        return imports_code
    
    def get_rest_endpoint(self, endpoints):
        endpoints_code = ""
        for endpoint in endpoints:
            endpoints_code += f"\n\t@{endpoint["method"].title()}Mapping(\"{endpoint["path"]}\")"
            params_and_vars = ""
            endpoints_code += f"""
    public Map<String, Object> {endpoint["name"]}(
        {params_and_vars}) {{
        Map<String, Object> data = new HashMap<>();
        data.put("message", "Hello, from {self.params["name"]}{endpoint["path"]}!");
        return data; // automatically converted to JSON
        }}\n"""
        return endpoints_code




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
    
    def get_artifact(self):
        return self.params["artifactId"].replace("-", "_")

    def update_db(self):
        db = Database("Framework", db_creds)
        data = self.params
        framework_id = data.pop("id")
        db.update_object(Springboot, framework_id, data)
