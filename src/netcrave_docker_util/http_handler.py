# IAmPaigeAT (paige@paige.bio) 2023

import asyncio
import json
import logging
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
        return (204, None, self.headers)

    @staticmethod
    async def get_post_data(request):
        log = logging.getLogger(__name__)
        if request.get("wsgi.input") is not None:
            data = json.loads(request.get("wsgi.input").read())
            log.debug(data)
            return data

    @staticmethod
    async def http_listener(cls, bind_host, port, sem=asyncio.Lock()):
        raise NotImplementedError()

    @staticmethod
    async def https_listener(cls, bind_host, port, cert_path, key_path, ca_cert_path, sem=asyncio.Lock()):
        raise NotImplementedError()

    @staticmethod
    async def internal_network_driver(cls, path, sock_name, sem=asyncio.Lock()):
        # await sem.acquire() ### XXX not sure if this is the best place to do this
        # sem.release()

        whole_path = "{path}/{sock_name}".format(
            path=path,
            sock_name=sock_name)

        Path(whole_path).unlink(missing_ok=True)

        await serve(
            cls,
            unix_socket="{path}".format(
                path=whole_path))
