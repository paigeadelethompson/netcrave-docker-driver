# IAmPaigeAT (paige@paige.bio) 2023

import os
import asyncio

"""
https://pypi.org/project/powerdns-client/
"""


class dns_daemon():
    def __init__(self):
        self._api_key = os.environ.get("X-API-Key")

    async def run(self):
        # client = docker.DockerClient(base_url = path)
        while True:
            await asyncio.sleep(1)
