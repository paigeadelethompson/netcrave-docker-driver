from aiohttp import web
import logging 

class handler():
    def __init__(self):
        self.headers = [("Content-Type", "application/vnd.docker.plugins.v1.2+json")]
        self.router = []
    def add_route(self, method, path, callback):
        self.router.append({"method": method, "path": path, "callback": callback})
