from utils import Folder, File
from arms.arm import get_arm
from arms.endpoints.endpoints import get_service_endpoints

class Flask:
    def __init__(self, framework_id):
        pass

    def create_framework(self, service_id, repo_type, repo_id):
        repo = get_arm("repo", repo_type, repo_id)

        files = self.get_files(service_id)

        repo.upload_files(files)
        
    def get_files(self, service_id):
        endpoints = get_service_endpoints(service_id)
        return [
            self.generate_app_file(endpoints),
            self.generate_requirements_file(),
            self.generate_dockerfile()
            ]

    def generate_app_file(self, endpoints):
        app_file = File("app.py")
        app_file.content += "from flask import Flask, request, jsonify\n\n"
        app_file.content += "app = Flask(__name__)\n\n"
        app_file.content += self.get_flask_endpoints(endpoints)
        app_file.content += "if __name__ == \"__main__\":\n\tapp.run(host=\"0.0.0.0\", debug=True)"
        return app_file

    def generate_requirements_file(self):
        requirements = File("requirements.txt")
        requirements.content = "flask\npytest"
        return requirements

    def get_flask_endpoints(self, endpoints):
        endpoint_str = ""
        for endpoint in endpoints:
            endpoint_str += f"@app.route(\"{endpoint['path']}\", methods=[\"{endpoint["method"]}\"])\n"
            endpoint_str += f"def {endpoint['name']}():\n\t"
            if endpoint["variables"]:
                endpoint_str += "data = request.json\n\t"
            return_str = f"reply from endpoint {endpoint['name']}"
            if endpoint["variables"]:
                return_str += f", data = {{data}}"
            endpoint_str += f"return jsonify(f\"{return_str}\")\n\n"
        return endpoint_str
    
    def generate_dockerfile(self):
        dockerfile = File("dockerfile")
        dockerfile.content = """# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
"""
        return dockerfile
    
    def get_test_files(self, test_type, endpoints):
        match test_type:
            case "Pytest":
                return self.get_pytest_tests_file(endpoints)

    def get_pytest_tests_file(self, endpoints):
            file = File("test_app.py")
            file.content = """
import json
import pytest
from app import app

@pytest.fixture
def client():
    \"\"\"Provides a test client for the Flask app.\"\"\"
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

"""

            for endpoint in endpoints:
                data = {}
                for var in endpoint["variables"]:
                    data[var["name"]] = get_random_value(var["type"])
                file.content += f"""
def test_{endpoint['name']}(client):
    response = client.{endpoint['method'].lower()}("{endpoint['path']}", json={data})
    assert response.status_code == 200
    assert json.loads(response.get_data()) == "reply from endpoint {endpoint['name']}"""
                if endpoint['variables']:
                    file.content += f", data = {data}"
                file.content += "\"\n"
            

            return [file]
    
def get_random_value(type):
    if type == "int":
        return 1
    elif type == "string":
        return "sample_string"