from mysql_database import Database
from variables import db_creds
import service.service as service


def create_services_connection(connection):
    db = Database("Map", db_creds)
    db.add_object("ServicesConnection", connection)
    dest_connections = db.get_list_of_objects("ServicesConnection", {"destination_service_id": connection["destination_service_id"]}, as_dict=True)
    dest_connections.extend(db.get_list_of_objects("ServicesConnection", {"source_service_id": connection["destination_service_id"]}, as_dict=True))
    service.configure_service_connections(connection["destination_service_id"], dest_connections)

    dest_connections = db.get_list_of_objects("ServicesConnection", {"destination_service_id": connection["source_service_id"]}, as_dict=True)
    dest_connections.extend(db.get_list_of_objects("ServicesConnection", {"source_service_id": connection["source_service_id"]}, as_dict=True))
    service.configure_service_connections(connection["source_service_id"], dest_connections)


def get_projects_connection(project_id):
    db = Database("Map", db_creds)
    connections = db.get_list_of_objects("ServicesConnection", {"project_id": project_id}, as_dict=True)
    return connections

def new_func():
    return None