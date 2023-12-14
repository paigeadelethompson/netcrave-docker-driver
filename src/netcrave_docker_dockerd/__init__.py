from netcrave_docker_dockerd.daemon import service
from netcrave_docker_dockerd.setup_environment import setup_environment

def daemon():
    service("netcrave-dockerd").start()
    
def install():
    service("netcrave-dockerd").create_service()
