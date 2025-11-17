from mysql_database import Database
from variables import db_creds

def get_container_service(service_id):
    db = Database("Service", db_creds)
    return db.get_object_by_id("ContainerService", service_id)