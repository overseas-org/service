

from arms.arm import create_service_arm, delete_service_arm, get_arm
from mysql_database import Database
from variables import db_creds

db = Database("Infrastructure", db_creds)

def write_to_db(infrastructure_type, info):
    variables = []
    if "variables" in info:
        variables = info.pop("variables")

    infra_id = db.add_object(infrastructure_type, info)

    if variables:
        for variable in variables:
                variable[infrastructure_type] = infra_id
                db.add_object(f"{infrastructure_type}Varriable", variable)
    return infra_id

def delete_from_db(infrastructure_type, infrastructure_id):
    variables = db.get_list_of_objects(f"{infrastructure_type}Varriable", {infrastructure_type: infrastructure_id})

    if variables:
        for variable in variables:
            db.delete_object(f"{infrastructure_type}Varriable", variable.id)
    db.delete_object(infrastructure_type, infrastructure_id)

def create_infrastructure(info, service_name, app, image, **args):
    info["image"] = image
    info["app"] = app
    return create_service_arm("infrastructure", info, write_to_db=write_to_db, service_name=service_name, **args)

def delete_infrastructure(infrastructure_type, infrastructure_id):
    delete_service_arm("infrastructure", infrastructure_type, infrastructure_id)
    delete_from_db(infrastructure_type, infrastructure_id)


def redefine_network_security(service_name, services_connections, infrastructure_type, infrastructure_id, **args):
    infra = get_arm("infrastructure", infrastructure_type, infrastructure_id)
    return infra.redefine_network_security(service_name, services_connections, **args)