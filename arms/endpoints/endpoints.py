
from mysql_database import Database
from variables import db_creds

db = Database("Endpoints", db_creds)

def create_endpoints(service_id, endpoints):
    for endpoint in endpoints:
        endpoint_type = endpoint.pop("endpoint_type")
        variables = endpoint.pop("variables")
        instance_endpoint_id = db.add_object(endpoint_type, endpoint)
        endpoint_id = db.add_object("Endpoint", {
            "endpoint_type": endpoint_type,
            "endpoint_id": instance_endpoint_id,
            "service_id": service_id
        })
        create_endpoint_variables(endpoint_id, variables)

def get_endpoints(service_id):
    res = []
    endpoints = db.get_list_of_objects("Endpoint", {"service_id": service_id})
    for endpoint in endpoints:
        instance_endpoint = db.get_object_by_id(endpoint.endpoint_type, endpoint.endpoint_id, as_dict=True)
        instance_endpoint["endpoint_type"] = endpoint.endpoint_type
        instance_endpoint["variables"] = get_endpoint_variables(endpoint.endpoint_id)
        res.append(instance_endpoint)
    return res

def create_endpoint_variables(endpoint_id, variables):
    for var in variables:
        var["endpoint_id"] = endpoint_id
        db.add_object("Variable", var)

def get_endpoint_variables(endpoint_id):
    return db.get_list_of_objects("Variable", {"endpoint_id": endpoint_id}, True)

def delete_endpoints(service_id):
    endpoints = db.get_list_of_objects("Endpoint", {"service_id": service_id})
    for endpoint in endpoints:
        variables = db.get_list_of_objects("Variable", {"endpoint_id": endpoint.id})
        for var in variables:
            db.delete_object("Variable", var.id)
        db.delete_object("Endpoint", endpoint.id)