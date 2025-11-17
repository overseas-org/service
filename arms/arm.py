import importlib

from mysql_database import Database
from variables import db_creds
from arms.errors import ArmExists
from utils import capatlize, decapatlize

def create_service_arm(arm, info, **args):
    arm_type = info.pop(f"{arm}_type")
    if "write_to_db" in args:
        write_to_db = args.pop("write_to_db")
        arm_id = write_to_db(arm_type, info)
    else:
        db = Database(capatlize(arm), db_creds)
        arm_id = db.add_object(arm_type, info)
    module = importlib.import_module(f"arms.{arm}.types.{decapatlize(arm_type)}")
    arm_obj = getattr(module, arm_type)(arm_id)
    try:
        if "exist" not in info or info["exists"] != "true":
            getattr(arm_obj, f"create_{arm}")(**args)
    except ArmExists:
        db.update_object(arm_type, arm_id, {"exist": "true"})
    return arm_id

def update_existens(database, table, id, existens="true"):
    db = Database(database, db_creds)
    db.update_object(table, id, {"exist": existens})

def get_arm(arm, arm_type, arm_id):
    arm_module = importlib.import_module(f"arms.{arm}.types.{decapatlize(arm_type)}")
    arm = getattr(arm_module, arm_type)(arm_id)
    return arm

def delete_service_arm(arm, arm_type, arm_id):
    arm_obj = get_arm(arm, arm_type, arm_id)
    getattr(arm_obj, f"delete_{arm}")()
