from arms.repo.repo import create_repo, delete_repo, add_webhook
from arms.image_registry.image_registry import create_image_registry, get_image, delete_image_registry
from arms.infrastructure.infrastructure import create_infrastructure, delete_infrastructure
from arms.pipeline.pipeline import create_pipeline, trigger_pipeline, delete_pipeline, get_pipeline_host
from arms.endpoints.endpoints import create_endpoints, delete_endpoints
from arms.framework.framework import create_framework
from arms.db.db import create_db
from mysql_database import Database
from multiprocessing import Process
from variables import db_creds
from service_comunications.progress import create_task, finish_step, start_step, start_task

class ContainerService:

    @classmethod
    def create_service(cls, parent_id, service_info):
        task_id = cls.create_service_creation_task(service_info)
        p = Process(target=cls.create_service_action, args=(parent_id, service_info, task_id))
        p.start()
        return task_id

    @classmethod
    def create_service_action(cls, parent_id, service_info, task_id):
        service_name = service_info["name"]
        db = Database("Service", db_creds)
        service_id = db.add_object("ContainerService", {"service_name": service_name})
        if "repo" in service_info and service_info["repo"]:
            start_step(task_id, "createRepo")
            try:
                repo_type = service_info["repo"]["repo_type"]
                repo_id = create_repo(service_info["repo"])
                db.update_object("ContainerService", service_id, {"repo_type": repo_type,
                                                    "repo_id": repo_id})
                finish_step(task_id, "createRepo")
            except:
                finish_step(task_id, "createRepo", False)
        else:
            raise Exception("Missing information: repo")
        if "image_type" in service_info and service_info["image_type"]:
            image_type = service_info["image_type"]
        else:
            image_type = "docker"
        db.update_object("ContainerService", service_id,{"image_type": image_type})
        if "image_registry" in service_info and service_info["image_registry"]:
            try:
                start_step(task_id, "createImageRepo")
                image_registry_type = service_info["image_registry"]["image_registry_type"]
                image_registry_id = create_image_registry(service_info["image_registry"])
                db.update_object("ContainerService", service_id,{"image_registry_type": image_registry_type,
                                                                "image_registry_id": image_registry_id})
                finish_step(task_id, "createImageRepo")
            except:
                finish_step(task_id, "createImageRepo", False)
        else:
            raise Exception("Missing information: image registry")
        if "infrastructure" in service_info and service_info["infrastructure"]:
            start_step(task_id, "createInfastructure")
            try:
                infrastructure_type = service_info["infrastructure"]["infrastructure_type"]
                image = get_image(image_registry_type, image_registry_id)
                infrastructure_id = create_infrastructure(service_info["infrastructure"], service_name, 
                                                        service_name, f"{image}:1.<version>", repo_type=repo_type, repo_id=repo_id)
                db.update_object("ContainerService", service_id,{"infrastructure_type": infrastructure_type,
                                                                "infrastructure_id": infrastructure_id})
                finish_step(task_id, "createInfastructure")
            except:
                finish_step(task_id, "createInfastructure", False)
        else:
            raise Exception("Missing information: infrastructure")
        if "pipeline" in service_info and service_info["pipeline"]:
            try:
                start_step(task_id, "createPipeline")
                pipeline_type = service_info["pipeline"]["pipeline_type"]
                pipeline_id = create_pipeline(service_info["pipeline"], service_id=service_id)
                add_webhook(repo_type, repo_id, get_pipeline_host(pipeline_type, pipeline_id))
                db.update_object("ContainerService", service_id, {"pipeline_type": pipeline_type,
                                                                "pipeline_id": pipeline_id})
                finish_step(task_id, "createPipeline")
            except:
                finish_step(task_id, "createPipeline", False)
        else:
            raise Exception("Missing information: pipeline")
        if "endpoints" in service_info and service_info["endpoints"]:
            create_endpoints(parent_id, service_info["endpoints"])
        if "language" in service_info and service_info["language"]:
            db.update_object("ContainerService", service_id, {"language": service_info["language"]})
        if "framework" in service_info and service_info["framework"]:
            start_step(task_id, "createCodeTemplate")
            try:
                framework_type = service_info["framework"]["framework_type"]
                framework_id = create_framework(service_info["framework"], service_id=parent_id, 
                                                repo_type=repo_type, repo_id=repo_id)
                db.update_object("ContainerService", service_id, {"framework_type": framework_type,
                                                                "framework_id": framework_id})
                finish_step(task_id, "createCodeTemplate")
            except:
                finish_step(task_id, "createCodeTemplate", False)
        if "db" in service_info and service_info["db"]:
            start_step(task_id, "createDb")
            try:
                db_id = create_db(service_info["db"], service_name=service_name, 
                                infrastructure_type=infrastructure_type,
                                infrastructure_id=infrastructure_id,
                                repo_type=repo_type, repo_id=repo_id
                                )
                db.update_object("ContainerService", service_id, {"db_id": db_id})
                finish_step(task_id, "createDb")
            except:
                finish_step(task_id, "createDb", False)
        start_step(task_id, "runningPipeline")
        try:
            trigger_pipeline(pipeline_type, pipeline_id)
            finish_step(task_id, "runningPipeline")
        except Exception as e:
            finish_step(task_id, "runningPipeline", False)
        db.update_object("Service", parent_id, {"service_type": "ContainerService",
                                            "service_id": service_id,})
        # db = Database("Service", db_creds)
        # service_id = db.add_object("ContainerService", service)
        return task_id
    
    @classmethod
    def delete_service(cls, service_id):
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

    @classmethod
    def create_service_creation_task(cls, service_info):
        task_steps = []
        if "repo" in service_info and service_info["repo"]:
            task_steps.append({
                    "name": "createRepo",
                    "description": "Creating code repository"
                })
        if "image_registry" in service_info and service_info["image_registry"]:
            task_steps.append({
                    "name": "createImageRepo",
                    "description": "Creating image repository"
                })
        if "infrastructure" in service_info and service_info["infrastructure"]:
            task_steps.append({
                    "name": "createInfastructure",
                    "description": "Creating and upload infastructure files (yamls)"
                })
        if "pipeline" in service_info and service_info["pipeline"]:
            task_steps.append({
                    "name": "createPipeline",
                    "description": "Creating pipeline"
                })
        if "framework" in service_info and service_info["framework"]:
            task_steps.append({
                    "name": "createCodeTemplate",
                    "description": "Creating and uploading code template"
                })
        if "db" in service_info and service_info["db"]:
            task_steps.append({
                "name": "createDb",
                "description": "Creating and uploading db infastructure files (yamls)"
            })
        task_steps.append({
                    "name": "runningPipeline",
                    "description": "running Pipeline"
                })
        task_id = create_task({
            "name": "createService",
            "steps": task_steps
        })
        start_task(task_id)
        return task_id
