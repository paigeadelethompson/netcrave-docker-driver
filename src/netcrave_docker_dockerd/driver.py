import hashlib
import json
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, ip_address
from hashlib import sha512
from netcrave_docker_util.exception import unknown
from netcrave_docker_util.http_handler import handler
from netcrave_docker_dockerd.setup_environment import get_NDB

class internal_driver(handler):
    def __init__(self):
        super().__init__()
        self._ndb = get_NDB()
        self.add_route(
            "POST", 
            "/Plugin.Activate", 
            self.plugin_activate)
        self.add_route(
            "POST",
            "/NetworkDriver.GetCapabilities",
            self.plugin_get_capabilities)
        self.add_route(
            "POST",
            "/NetworkDriver.CreateNetwork",
            self.plugin_create_network)
        self.add_route(
            "POST",
            "/NetworkDriver.DeleteNetwork",
            self.plugin_delete_network)
        self.add_route(
            "POST",
            "/NetworkDriver.CreateEndpoint",
            self.plugin_create_endpoint)
        self.add_route("POST", "/NetworkDriver.Join", self.plugin_join)
        self.add_route(
            "POST",
            "/NetworkDriver.ProgramExternalConnectivity",
            self.plugin_program_external_connectivity)
        self.add_route(
            "POST",
            "/NetworkDriver.EndpointOperInfo",
            self.plugin_endpoint_oper_info)
        self.add_route(
            "POST",
            "/NetworkDriver.DeleteEndpoint",
            self.plugin_delete_endpoint)
        self.add_route("POST", "/NetworkDriver.Leave", self.plugin_leave)
        self.add_route(
            "POST",
            "/NetworkDriver.DiscoverNew",
            self.plugin_discover_new)
        self.add_route(
            "POST",
            "/NetworkDriver.DiscoverDelete",
            self.plugin_discover_delete)
        self.add_route(
            "POST",
            "/NetworkDriver.RevokeExternalConnectivity",
            self.plugin_revoke_external_connectivity)

    async def plugin_activate(self, request):
        return (
            200,
            json.dumps({"Implements": ["NetworkDriver"]}),
            [])

    async def plugin_get_capabilities(self, request):
        return (
            200,
            json.dumps({"Scope": "local"}),
            [])

    async def plugin_create_network(self, request):

        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_delete_network(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_create_endpoint(self, request):
        data = json.loads(request.data)
        interface = data.get("Interface")

        sha = sha512()
        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id=data.get("EndpointID"),
            network_id=data.get("NetworkID")))

        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id=data.get("EndpointID"),
            network_id=data.get("NetworkID")))

        v4 = IPv4Network(interface.get("Address"))
        v6 = IPv6Network(interface.get("AddressV6"))

        candidates = []

        for index in self._ndb.addresses.dump():
            current = self._ndb.addresses.get(index)
            if isinstance(ip_address(current),
                          IPv6Address) and IPv6Address(current).is_link_local:
                continue
            elif isinstance(ip_address(current), IPv6Address):
                if IPv6Network(ip_address(current), 128).subnet_of(v6):
                    candidates.append(index)
            elif isinstance(ip_address(current), IPv4Address):
                if IPv4Network(ip_address(current), 32).subnet_of(v4):
                    candidates.append(index)

        if len(set([index.get("index") for index in candidates])) != 1:
            raise unknown(
                "requested /128 address is a subnet of more than one allocated /30 network")

        v4_out, v6_out = sorted(candidates, lambda index: index.get("family"))

        selected_interface = next(
            (self._ndb.interfaces.get(index).get("address")
             for index in self._ndb.interfaces.dump()
             if self._ndb.interfaces.get(index).get("ifname") == index.get("label")))

        selected_interface.set("ifalias", sha.hexdigest())
        selected.interface.commit()

        return (
            200,
            json.dumps({
                "Interface":
                    {
                        "Address": str(IPv4Address(v4_out)),
                        "AddressV6": str(IPv6Address(v6_out)),
                        "MacAddress": selected_interface.get("address"),
                    }
            }),
            [])

    async def plugin_join(self, request):

        return (
            200,
            json.dumps(json.dumps({
                'InterfaceName': {
                    'SrcName': None,
                    'DstPrefix': 'eth',
                    'Gateway': None}}),
                []))

    async def plugin_program_external_connectivity(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_endpoint_oper_info(self, request):
        data = json.loads(request.data)
        endpoint_id = data.get("EndpointID")
        network_id = data.get("NetworkID")

        sha = sha512()

        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id=data.get("EndpointID"),
            network_id=data.get("NetworkID")))

        oper = next((self._ndb.interfaces.get(index)
                    for index in self._ndb.interfaces.dump()
                    if index["iflias"] == sha.hexdigest()))

        net = next((self._ndb.addresses.get(index)
                    for index in self._ndb.addresses.dump()
                    if self._ndb.addresses.get(index).get("label") == oper.get("ifname")))

        network = IPv4Network(
            "{addr}/32".format(
                addr=net.get(
                    "address"))).supernet(
                        new_prefix=net.get("prefixlen"))

        return (
            200,
            json.dumps({
                "Value": {
                    endpoint_id: oper.get("ifname"),
                    network_id: str(network)}}),
            [])

    async def plugin_delete_endpoint(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_leave(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_discover_new(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_discover_delete(self, request):
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_revoke_external_connectivity(self, request):
        return (
            200,
            json.dumps(dict()),
            [])
