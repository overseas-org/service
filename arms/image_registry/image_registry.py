from arms.arm import create_service_arm, delete_service_arm
from arms.arm import get_arm 

def create_image_registry(info):
    return create_service_arm("image_registry", info)

def delete_image_registry(image_registry_type, image_registry_id):
    return delete_service_arm("image_registry", image_registry_type, image_registry_id)

def get_image(image_registry_type, image_registry_id):
    image_registry = get_arm("image_registry", image_registry_type, image_registry_id)
    return image_registry.get_image()