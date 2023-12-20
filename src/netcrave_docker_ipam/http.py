from netcrave_docker_util.http_handler import handler


class ipam_driver(handler):
    def __init__(self):
        super().__init__()
        self.add_route("POST", '/Plugin.Activate', self.Activate)
        self.add_route(
            "POST",
            '/IpamDriver.GetCapabilities',
            self.GetCapabilities)
        self.add_route(
            "POST",
            '/IpamDriver.GetDefaultAddressSpaces',
            self.GetDefaultAddressSpaces)
        self.add_route("POST", '/IpamDriver.RequestPool', self.RequestPool)
        self.add_route("POST", '/IpamDriver.ReleasePool', self.ReleasePool)
        self.add_route(
            "POST",
            '/IpamDriver.RequestAddress',
            self.RequestAddress)
        self.add_route(
            "POST",
            '/IpamDriver.ReleaseAddress',
            self.ReleaseAddress)

    def Activate(self, request):
        raise NotImplementedError()

    def GetCapabilities(self, request):
        raise NotImplementedError()

    def GetDefaultAddressSpaces(self, request):
        raise NotImplementedError()

    def RequestPool(self, request):
        raise NotImplementedError()

    def ReleasePool(self, request):
        raise NotImplementedError()

    def RequestAddress(self, request):
        raise NotImplementedError()

    def ReleaseAddress(self, request):
        raise NotImplementedError()
