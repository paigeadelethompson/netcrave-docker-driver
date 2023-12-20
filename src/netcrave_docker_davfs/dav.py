from netcrave_docker_util.http_handler import handler

class dav_filesystem_service(handler):
    def __init__(self):
        super().__init__()
        self.add_route("LOCK", "/", self.lock)
        self.add_route("PROPFIND", "/", self.prop_find)
        self.add_route("PROPPATCH", "/", self.pro_patch)
        self.add_route("MKCOL", "/", self.make_collection)
        self.add_route("COPY", "/", self.copy)
        self.add_route("MOVE", "/", self.move)
        self.add_route("GET", "/", self.get)
        self.add_route("PUT", "/", self.put)
        self.add_route("DELETE", "/", self.delete)
        self.add_route("UNLOCK", "/", self.unlock)
        
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
