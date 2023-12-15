from netcrave_docker_dockerd.daemon import service

def daemon():
    service("netcrave-dockerd").start()
    
def install():
    service("netcrave-dockerd").create_service()
