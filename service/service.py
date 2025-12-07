import importlib
from mysql_database import Database
from variables import db_creds
from utils import decapatlize


def create_service(service_info):
    db = Database("Service", db_creds)
    service_type = service_info.pop("service_type")
    service_id = db.add_object("Service", {"service_name": service_info["name"], 
                                           "project_id": service_info["project"],
                                           "service_type": service_type,
                                           "version": service_info["version"]})
    # try:
    task_id = get_service_class(service_type).create_service(service_id, service_info)
    # db.update_object("Service", service_id, {"service_type": service_type,
    #                                         "service_id": instance_service_id,})
    # except Exception as e:
    #     print(e)
    #     db.delete_object("Service", service_id)
    return task_id

def delete_service(service_id):
    db = Database("Service", db_creds)
    service = db.get_object_by_id("Service", service_id)
    get_service_class(service.service_type).delete_service(service.service_id)
    db.delete_object("Service", service_id)

def get_service_class(service_type):
    service_type_module = importlib.import_module(f"service.types.{decapatlize(service_type)}")
    service_class = getattr(service_type_module, service_type)
    return service_class

def get_services(project_id, filter):
	db = Database("Service", db_creds)
	services = db.get_filtered_list_of_objects("Service", filter, include_columns=["service_name", "service_type"],
                                             as_dict=True, conditions={"project_id": project_id})
	return services

def get_service(service_id):
    db = Database("Service", db_creds)
    service = db.get_object_by_id("Service", service_id)
    service = db.get_object_by_id(service.service_type, service.id, as_dict=True)
    return service