from netcrave_docker_davfs.dav import dav_filesystem_service
from netcrave_docker_certificatemgr.service import memory_filesystem_service

class certificate_manager_service(dav_filesystem_service):
    def lock(self, request):
        raise NotImplementedError()

    def prop_find(self, request):
        raise NotImplementedError()

    def proppatch(self, request):
        raise NotImplementedError()

    def make_collection(self, request):
        raise NotImplementedError()

    def copy(self, request):
        raise NotImplementedError()

    def move(self, request):
        raise NotImplementedError()

    def get(self, request):
        raise NotImplementedError()

    def put(self, request):
        raise NotImplementedError()

    def delete(self, request):
        raise NotImplementedError()

    def unlock(self, request):
        raise NotImplementedError()
