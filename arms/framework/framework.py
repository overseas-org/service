
from arms.arm import create_service_arm 


def create_framework(info, **args):
    return create_service_arm("framework", info, **args)