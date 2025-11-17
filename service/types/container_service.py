from arms.repo.repo import create_repo, delete_repo, add_webhook
from arms.image_registry.image_registry import create_image_registry, get_image, delete_image_registry
from arms.infrastructure.infrastructure import create_infrastructure, delete_infrastructure
from arms.pipeline.pipeline import create_pipeline, trigger_pipeline, delete_pipeline, get_pipeline_host
from arms.endpoints.endpoints import create_endpoints, delete_endpoints
from arms.framework.framework import create_framework
from arms.db.db import create_db
from mysql_database import Database
from variables import db_creds

class ContainerService:

    def create_service(parent_id, service_info):
        service_name = service_info["name"]
        db = Database("Service", db_creds)
        service_id = db.add_object("ContainerService", {"service_name": service_name})
        if "repo" in service_info:
            repo_type = service_info["repo"]["repo_type"]
            repo_id = create_repo(service_info["repo"])
            db.update_object("ContainerService", service_id, {"repo_type": repo_type,
                                                "repo_id": repo_id})
        else:
            raise Exception("Missing information: repo")
        if "image_type" in service_info:
            image_type = service_info["image_type"]
        else:
            image_type = "docker"
        db.update_object("ContainerService", service_id,{"image_type": image_type})
        if "image_registry" in service_info:
            image_registry_type = service_info["image_registry"]["image_registry_type"]
            image_registry_id = create_image_registry(service_info["image_registry"])
            db.update_object("ContainerService", service_id,{"image_registry_type": image_registry_type,
                                                            "image_registry_id": image_registry_id})
        else:
            raise Exception("Missing information: image registry")
        if "infrastructure" in service_info:
            infrastructure_type = service_info["infrastructure"]["infrastructure_type"]
            image = get_image(image_registry_type, image_registry_id)
            infrastructure_id = create_infrastructure(service_info["infrastructure"], service_name, 
                                                      service_name, f"{image}:1.<version>", repo_type=repo_type, repo_id=repo_id)
            db.update_object("ContainerService", service_id,{"infrastructure_type": infrastructure_type,
                                                            "infrastructure_id": infrastructure_id})
        else:
            raise Exception("Missing information: infrastructure")
        if "pipeline" in service_info:
            pipeline_type = service_info["pipeline"]["pipeline_type"]
            pipeline_id = create_pipeline(service_info["pipeline"], service_id=service_id)
            add_webhook(repo_type, repo_id, get_pipeline_host(pipeline_type, pipeline_id))
            db.update_object("ContainerService", service_id, {"pipeline_type": pipeline_type,
                                                            "pipeline_id": pipeline_id})
        else:
            raise Exception("Missing information: pipeline")
        if "endpoints" in service_info:
            create_endpoints(parent_id, service_info["endpoints"])
        if "language" in service_info:
            db.update_object("ContainerService", service_id, {"language": service_info["language"]})
        if "framework" in service_info:
            framework_type = service_info["framework"]["framework_type"]
            framework_id = create_framework(service_info["framework"], service_id=parent_id, 
                                            repo_type=repo_type, repo_id=repo_id)
            db.update_object("ContainerService", service_id, {"framework_type": framework_type,
                                                            "framework_id": framework_id})
        if "db" in service_info and service_info["db"]:
            db_id = create_db(service_info["db"], service_name=service_name, 
                              infrastructure_type=infrastructure_type,
                              infrastructure_id=infrastructure_id,
                              repo_type=repo_type, repo_id=repo_id
                              )
            db.update_object("ContainerService", service_id, {"db_id": db_id})
        trigger_pipeline(pipeline_type, pipeline_id)
        # db = Database("Service", db_creds)
        # service_id = db.add_object("ContainerService", service)
        return service_id
    
    def delete_service(service_id):
        db = Database("Service", db_creds)
        service = db.get_object_by_id("ContainerService", service_id)
        if not service:
            return
        if service.repo_type and service.repo_id:
            delete_repo(service.repo_type, service.repo_id)
            db.delete_object_attributes("ContainerService", service_id, ["repo_type",
                                                                        "repo_id"])
        if service.image_registry_type and service.image_registry_id:
            delete_image_registry(service.image_registry_type, service.image_registry_id)
            db.delete_object_attributes("ContainerService", service_id, ["image_registry_type",
                                                                        "image_registry_id"])
        if service.infrastructure_type and service.infrastructure_id:
            delete_infrastructure(service.infrastructure_type, service.infrastructure_id)
            db.delete_object_attributes("ContainerService", service_id, ["infrastructure_type",
                                                                        "infrastructure_id"])
        if service.pipeline_type and service.pipeline_id:
            delete_pipeline(service.pipeline_type, service.pipeline_id)
            db.delete_object_attributes("ContainerService", service_id, ["pipeline_type",
                                                                        "pipeline_id"])
        # if service.db_id:
        #     delete_db(service.db)
        #     db.delete_object_attribute("ContainerService", service_id, "db_id")
        delete_endpoints(service_id)
        db.delete_object("ContainerService", service_id)
