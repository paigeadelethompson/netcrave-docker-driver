from aiohttp import web
from pathlib import Path
from netcrave_docker_util.http import serve


class handler():
    def __init__(self):
        self.router = []
        self.headers = [
            ("Content-Type", "application/vnd.docker.plugins.v1.2+json")]
        self.add_route("HEAD", "/.netcrave/health-check", self.health_check)

    def add_route(self, method, path, callback):
        self.router.append(
            {"method": method, "path": path, "callback": callback})

    async def health_check(self, request):
        return (204, None, headers)

    async def internal_network_driver(sem, cls, path, sock_name):
        await sem.acquire()
        sem.release()

        whole_path = "{path}/{sock_name}".format(
            path=path, sock_name=sock_name)
        Path(whole_path).unlink(missing_ok=True)

        await serve(
            cls,
            unix_socket="{path}".format(
                path=whole_path))
