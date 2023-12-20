import os
import docker
import asyncio
import powerdns_client
from powerdns_client.rest import ApiException

"""
https://pypi.org/project/powerdns-client/
"""


class dns_daemon():
    def __init__(self):
        self._api_key = os.environ.get("X-API-Key")

    async def run():
        # client = docker.DockerClient(base_url = path)
        while True:
            await asyncio.sleep(1)
