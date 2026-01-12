from utils import Folder, File, ByteFile
import os
from arms.arm import get_arm
from arms.endpoints.endpoints import get_service_endpoints

class React:
    def __init__(self, framework_id):
        pass

    def create_framework(self, service_id, repo_type, repo_id):
        repo = get_arm("repo", repo_type, repo_id)

        files = self.get_files(service_id)

        repo.upload_files(files)
        
    def get_files(self, service_id):
        files = []
        files.extend(self.create_react_app())
        files.append(self.generate_dockerfile())
        return files

    def create_react_app(self):
        template_location = "arms/framework/types/react_template"
        ret_files = []
        for root, dirs, files in os.walk(template_location):
            for name in files:
                full_file_path = "/".join([root, name]).removeprefix(f"{template_location}").removeprefix("\\").removeprefix("/")
                try:
                    with open(os.path.join(root, name), "r") as f:
                        ret_files.append(File(full_file_path, f.read()))
                except:
                    with open(os.path.join(root, name), "rb") as f:
                        ret_files.append(ByteFile(full_file_path, f.read()))
        return ret_files

    def generate_dockerfile(self):
        dockerfile = File("dockerfile")
        dockerfile.content = """# Use an official lightweight Python image
# -------- Build stage --------
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first (better caching)
COPY package*.json ./

RUN npm install

# Copy rest of the app
COPY . .

# Build the React app
RUN npm run build


# -------- Runtime stage --------
FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy build output to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
"""
        return dockerfile