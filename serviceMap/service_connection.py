from mysql_database import Database
from variables import db_creds

def create_services_connection(connection):
    db = Database("Map", db_creds)
    db.add_object("ServicesConnection", connection)

def get_projects_connection(project_id):
    db = Database("Map", db_creds)
    connections = db.get_list_of_objects("ServicesConnection", {"project_id": project_id}, as_dict=True)
    return connections