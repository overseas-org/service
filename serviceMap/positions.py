from mysql_database import Database
from variables import db_creds

def get_position(project_id):
    db = Database("Map", db_creds)
    results = {}
    positions = db.get_list_of_objects("Position", {"project_id": project_id}, as_dict=True)
    for position in positions:
        service_id = position["service_id"]
        del position["service_id"]
        results[str(service_id)] = position
    return results

# def create_positions(project_id, positiotns):
#     for service, position in positiotns.items():
#         position["service_id"] = int(service)
#         position["project_id"] = project_id
#         db = Database("Map")
#         db.add_object("Position", position)

def update_positions(positiotns):
    for service, position in positiotns.items():
        position["service_id"] = int(service)
        position_id = position["id"]
        del position["id"]

        db = Database("Map", db_creds)
        
        db.update_object("Position", position_id ,position)

def create_positions(project_id, service_id):

    db = Database("Map", db_creds)
    
    db.add_object("Position" , {"project_id": project_id,
                                "service_id": service_id,
                                "x": 100,
                                "y": 100})