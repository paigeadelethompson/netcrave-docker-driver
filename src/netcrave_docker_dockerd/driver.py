# IAmPaigeAT (paige@paige.bio) 2023
import asyncio
import json
import logging
import sys
import itertools
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, ip_address
from pathlib import Path
from hashlib import sha512
from netcrave_docker_util.exception import unknown
from netcrave_docker_util.http_handler import handler
from netcrave_docker_util.ndb import network_database


class internal_driver(handler):
    def __init__(self):
        super().__init__()
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
        log = logging.getLogger(__name__)
        return (
            200,
            json.dumps({"Implements": ["NetworkDriver"]}),
            [])

    async def plugin_get_capabilities(self, request):
        log = logging.getLogger(__name__)
        return (
            200,
            json.dumps({"Scope": "local"}),
            [])

    async def _get_interface_by_address(self, ndb, address):
        log = logging.getLogger(__name__)
        log.debug(address)
        return next((ndb.interfaces.get(index) for index in ndb.interfaces.dump() 
                     if address.get("label") == ndb.interfaces.get(index).get("ifname")))
        
    async def _get_network_and_interface(self, network_id, data, kind = type(IPv4Network)):
        log = logging.getLogger(__name__)
        address_space = data.get("AddressSpace")
        gateway = data.get("Gateway")
        pool = data.get("Pool")
        async with network_database() as ndb:
            if kind == type(IPv4Network):
                p = IPv4Network(pool)
                log.debug("pool {}".format(p))
                g = IPv4Network(str(next(itertools.islice(gateway.split("/"), 0, sys.maxsize))), 32).hosts().pop()
                log.debug("gateway {}".format(g))
                a = next(next(p.address_exclude(IPv4Network(g, 32))).hosts())
                log.debug("address to lookup {}".format(a))
                _a = next((ndb.addresses.get(index) for index in ndb.addresses.dump() 
                           if ip_address(ndb.addresses.get(index).get("address")) == a))
                log.debug("found NDB address {}".format(_a))
                return await self._get_interface_by_address(ndb, _a), a, p
            elif kind == type(IPv6Network):
                p = IPv6Network(pool)
                log.debug("pool {}".format(p))
                g = IPv6Network(str(next(itertools.islice(gateway.split("/"), 0, sys.maxsize))), 128).hosts().pop()
                log.debug("gateway {}".format(g))
                a = next(next(p.address_exclude(IPv6Network(g, 128))).hosts())
                log.debug("address to lookup {}".format(a))
                _a = next((ndb.addresses.get(index) for index in ndb.addresses.dump() 
                           if ip_address(ndb.addresses.get(index).get("address")) == a))
                log.debug("found NDB address {}".format(_a))
                return await self._get_interface_by_address(ndb, _a), a, p
            
    async def plugin_create_network(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        options = data.get("Options")
        ipv4_data = data.get("IPv4Data")
        ipv6_data = data.get("IPv6Data")
        
        for index in ipv4_data:
            log.debug(index)
            result = await self._get_network_and_interface(network_id, index, type(IPv4Network))
            if result is None:
                return (500, json.dumps(dict()), [])
        
        for index in ipv6_data:
            log.debug(index)
            result = await self._get_network_and_interface(network_id, index, type(IPv6Network))
            if result is None:
                return (500, json.dumps(dict()), [])
            
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
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")
        interfaces = data.get("Interface")
        address = interfaces.get("Address")
        address_ipv6 = interfaces.get("AddressIPv6")
        options = data.get("Options")
        
        async with network_database() as ndb:
            n = IPv4Network(str(next(itertools.islice(address.split("/"), 0, 
                                                        sys.maxsize))), 32)
            a = n.hosts().pop()
            
            prefixlen = str(next(itertools.islice(address.split("/"), 1, 
                                                  sys.maxsize)))
            
            _a = next((ndb.addresses.get(index) for index in ndb.addresses.dump() 
                    if ip_address(ndb.addresses.get(index).get("address")) == a))
            
            intf = await self._get_interface_by_address(ndb, _a)
            
            log.debug("address: {} mac-address: {}".format(_a.get("address"), 
                                                            intf.get("address")))
            
            intf.set("ifalias", "{}{}".format(network_id, endpoint_id))
            intf.commit()
            return (200, json.dumps({"Interface": {
                "MacAddress": intf.get("address") }}), [])

    async def plugin_join(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")
        sandbox_key = data.get("SandboxKey")
        options = data.get("Options")
        
        Path(sandbox_key).unlink(missing_ok=True)
        Path(sandbox_key).link_to("/run/netns/_netcrave")
        async with network_database() as ndb:
            intf = next((ndb.interfaces.get(index) for index in ndb.interfaces.dump()
                        if "{}{}".format(network_id, endpoint_id) == ndb.interfaces.get(index).get("ifalias")))
            
            return (
                200,
                json.dumps(dict({"InterfaceName": {"SrcName": intf.get("ifname"), 
                                                "DstPrefix": ""}, "Gateway": "", 
                "GatewayIPv6": "", "StaticRoutes": []})), [])

    async def plugin_program_external_connectivity(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        return (
            200,
            json.dumps(dict()),
            [])

    async def plugin_endpoint_oper_info(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        return (
            200,
            json.dumps(dict()),
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
