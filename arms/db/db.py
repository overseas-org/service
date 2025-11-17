from mysql_database import Database
from variables import db_creds
from arms.infrastructure.infrastructure import create_infrastructure
from arms.infrastructure.types.kubernetes_deployment import KubernetesDeployment

db = Database("ServiceDb", db_creds)

def create_db(info, service_name, infrastructure_type, infrastructure_id, **args):
    db_type = info.pop("db_type")
    db_flavor = info.pop("db_flavor")
    match db_type:
        case "KubernetesDeployment":
            if infrastructure_type == "KubernetesDeployment":
                infrastructure = KubernetesDeployment(infrastructure_id)
            # infrastructure_db = Database("Infrastructure", db_creds)
            info["infrastructure_type"] = db_type
            info["image"] = db_flavor
            info["app"] = f"{service_name}-db"
            info["include_service"] = "true"
            info["connector_id"] = infrastructure.connector_id
            info["namespace"] = infrastructure.namespace
            if db_flavor == "mysql":
                info["port"] = 3306
                info["variables"] = [
                {
                    "name": "MYSQL_ROOT_PASSWORD",
                    "value": info.pop("root_password")
                }
            ]
            else: 
                info.pop("root_password")
    db_infrastructure_id = create_infrastructure(info, service_name, f"{service_name}-db", db_flavor, **args)
    service_id = db.add_object("ServiceDb", {
        "db_type": db_type,
        "db_flavor": db_flavor,
        "infrastructure_id": db_infrastructure_id
    })
    return service_id
    # match db_type:
    #     case "KubernetesDeployment":
    #         infrastructure_db = Database("Infrastructure", db_creds)
    #         info["image"] = db_flavor
    #         info["app"] = f"{service_name}-db"
    #         info["include_service"] = "true"
    #         info["connector_id"] = connector_id
    #         if db_flavor == "mysql":
    #             info["port"] = 3306
    #             info[]
    #         kubernetes_deployment_id = infrastructure_db.add_object("KubernetesDeployment", info)
    #         deployment = KubernetesDeployment(kubernetes_deployment_id)
    #         deployment.create_infrastructure(service_name, repo_type, repo_id)

