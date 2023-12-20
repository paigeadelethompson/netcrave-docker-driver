# IAmPaigeAT (paige@paige.bio) 2023

from netcrave_docker_util.http_handler import handler


class network_driver(handler):
    def __init__(self):
        super().__init__()
        self.add_route("POST", '/Plugin.Activate', self.plugin_activate)
        self.add_route(
            "POST",
            '/NetworkDriver.GetCapabilities',
            self.plugin_get_capabilities)
        self.add_route(
            "POST",
            '/NetworkDriver.CreateNetwork',
            self.plugin_create_network)
        self.add_route(
            "POST",
            '/NetworkDriver.DeleteNetwork',
            self.plugin_delete_network)
        self.add_route(
            "POST",
            '/NetworkDriver.CreateEndpoint',
            self.plugin_create_endpoint)
        self.add_route(
            "POST",
            '/NetworkDriver.EndpointOperInfo',
            self.plugin_endpoint_oper_info)
        self.add_route(
            "POST",
            '/NetworkDriver.DeleteEndpoint',
            self.plugin_delete_endpoint)
        self.add_route("POST", '/NetworkDriver.Join', self.plugin_join)
        self.add_route("POST", '/NetworkDriver.Leave', self.plugin_leave)
        self.add_route(
            "POST",
            '/NetworkDriver.DiscoverNew',
            self.plugin_discover_new)
        self.add_route(
            "POST",
            '/NetworkDriver.DiscoverDelete',
            self.plugin_discover_delete)
        self.add_route(
            "POST",
            '/NetworkDriver.ProgramExternalConnectivity',
            self.plugin_program_external_connectivity)
        self.add_route(
            "POST",
            '/NetworkDriver.RevokeExternalConnectivity',
            self.plugin_revoke_external_connectivity)

    def plugin_activate(self, request):
        raise NotImplementedError()

    def plugin_get_capabilities(self, request):
        raise NotImplementedError()

    def plugin_create_network(self, request):
        raise NotImplementedError()

    def plugin_delete_network(self, request):
        raise NotImplementedError()

    def plugin_create_endpoint(self, request):
        raise NotImplementedError()

    def plugin_endpoint_oper_info(self, request):
        raise NotImplementedError()

    def plugin_delete_endpoint(self, request):
        raise NotImplementedError()

    def plugin_join(self, request):
        raise NotImplementedError()

    def plugin_leave(self, request):
        raise NotImplementedError()

    def plugin_discover_new(self, request):
        raise NotImplementedError()

    def plugin_discover_delete(self, request):
        raise NotImplementedError()

    def plugin_program_external_connectivity(self, request):
        raise NotImplementedError()

    def plugin_revoke_external_connectivity(self, request):
        raise NotImplementedError()
