import os
import docker
import time 
import powerdns_client
import asyncio
from powerdns_client.rest import ApiException

"""
https://pypi.org/project/powerdns-client/
"""
class dns_daemon():
    def __init__(self):
        self._api_key = os.environ.get("X-API-Key")
        pass
    
    async def main():
        #client = docker.DockerClient(base_url = path)
        while True:
            time.sleep(1)

