from mysql_database import Database
from variables import db_creds
import service.service as service


def create_services_connection(connection):
    db = Database("Map", db_creds)
    connection_id = db.add_object("ServicesConnection", connection)
    try:
        rollout_service_connections(connection["destination_service_id"])
        rollout_service_connections(connection["source_service_id"])
    except Exception as e:
        db.delete_object("ServicesConnection", connection_id)
    return connection_id


def rollout_service_connections(service_id):
    db = Database("Map", db_creds)
    service_connections = db.get_list_of_objects("ServicesConnection", {"destination_service_id": service_id}, as_dict=True)
    service_connections.extend(db.get_list_of_objects("ServicesConnection", {"source_service_id": service_id}, as_dict=True))
    service.configure_service_connections(service_id, service_connections)


def delete_services_connection(connection_id):
    db = Database("Map", db_creds)
    connection = db.get_object_by_id("ServicesConnection", connection_id, as_dict=True)
    db.delete_object("ServicesConnection", connection_id)
    try:
        rollout_service_connections(connection["destination_service_id"])
        rollout_service_connections(connection["source_service_id"])
    except Exception as e:
        db.add_object("ServicesConnection", {k: v for k, v in connection.items() if v is not None})
        raise Exception("Failed to delete connection")

    

def get_projects_connection(project_id):
    db = Database("Map", db_creds)
    connections = db.get_list_of_objects("ServicesConnection", {"project_id": project_id}, as_dict=True)
    return connections


def get_connection(connection_id):
    db = Database("Map", db_creds)
    connection = db.get_object_by_id("ServicesConnection", connection_id, as_dict=True)
    return connection