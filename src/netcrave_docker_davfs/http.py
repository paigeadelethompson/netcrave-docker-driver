import os
from netcrave_docker_util.http_handler import handler


class filesystem_driver(handler):
    def __init__(self):
        super().__init__()
        self.add_route("POST", '/Plugin.Activate', self.activate)
        self.add_route("POST", '/VolumeDriver.Create', self.create)
        self.add_route("POST", '/VolumeDriver.Remove', self.remove)
        self.add_route("POST", '/VolumeDriver.Path', self.path)
        self.add_route("POST", '/VolumeDriver.Mount', self.mount)
        self.add_route("POST", '/VolumeDriver.Unmount', self.unmount)
        self.add_route("POST", '/VolumeDriver.List', self.list)
        self.add_route("POST", '/VolumeDriver.Get', self.get)

    def activate(request):
        raise NotImplementedError()

    def create(request):
        raise NotImplementedError()

    def remove(request):
        raise NotImplementedError()

    def path(request):
        raise NotImplementedError()

    def mount(request):
        raise NotImplementedError()

    def unmount(request):
        raise NotImplementedError()

    def list(request):
        raise NotImplementedError()

    def get(request):
        raise NotImplementedError()

    def capabilities(request):
        raise NotImplementedError()
