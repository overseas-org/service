


import service.service as service

def create_service():
    data = {
        "name": "greet",
        "project": 1,
        "service_type": "ContainerService",
        "version": 1,
        "repo": {
            "name": "greet",
            "connector_id": 1,
            "repo_type": "Github"
        },
        "image_registry": {
            "image_registry_type": "Dockerhub",
            "image_name": "greet",
            "connector_id": 4
        },
        "image_type": "docker",
        "infrastructure": {
            "infrastructure_type": "KubernetesDeployment",
            "connector_id": 30,
            "namespace": "new-test",
            "port": "5000",
            "include_autoScale": "true",
            "include_service": "true",
            "min_replicas": "1",
            "max_replicas": "2",
            "include_pv": "true",
            "pv_storage_class": "local-path",
            "pv_storage_path": "/data/dbs-local-storage/greet",
            "storage_amount": "1Gi",
            "variables": [
                {
                    "name": "name",
                    "value": "hanna"
                }
            ],
        },
        "pipeline": {
            "pipeline_type": "Jenkins",
            "connector_id": 14,
            "folder": "new-test",
            "name": "greet"
        },
        "endpoints": [
            {
                "endpoint_type": "RestApi",
                "name": "hello",
                "path": "/hello",
                "method": "GET",
                "variables": [
                    {
                        "name": "name",
                        "type": "string",
                        "optional": "true"
                    }
                ]
            }
        ],
        "language": "python",
        "framework": {
            "framework_type": "Flask"
        },
        "db": {
            "db_type": "KubernetesDeployment",
            "db_flavor": "mysql",
            "root_password": "rootpw",
            "include_autoScale": "true",
            "min_replicas": "1",
            "max_replicas": "2",
            "include_pv": "true",
            "pv_storage_class": "local-path",
            "pv_storage_path": "/data/dbs-local-storage/greet",
            "pv_mount_path": "/var/lib/mysql",
            "storage_amount": "1Gi"
        }
    }
    # service.delete_service(1)
    # service.delete_service(2)
    service_id = service.create_service(data)
    return service_id
    
        


id = create_service()
print(id)