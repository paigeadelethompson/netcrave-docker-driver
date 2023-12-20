from netcrave_docker_davfs.dav import davfs_http

"""
This is the actual DAV server that can be implemented by services like certificatemgr
to provide a file system for example containing issued certificates stored on CRDB
and cached on MemoryFS
"""

dav_http = netcrave_flask()


@dav_http.route('/', methods=["LOCK"])
def lock(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["PROPFIND"])
def propfind(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["PROPPATCH"])
def proppatch(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["MKCOL"])
def make_collection(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["COPY"])
def copy(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["MOVE"])
def move(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["GET"])
def get(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["PUT"])
def put(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["DELETE"])
def delete(request):
    raise NotImplementedError()


@dav_http.route('/', methods=["UNLOCK"])
def unlock(request):
    raise NotImplementedError()
