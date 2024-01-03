# IAmPaigeAT (paige@paige.bio) 2023
import asyncio
import json
import logging
import sys
import itertools
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, ip_address
from pathlib import Path
from hashlib import sha512
from netcrave_docker_util.http_handler import handler
from netcrave_docker_util.ndb import network_database
from netcrave_docker_dockerd.setup_environment import enumerate_networks

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

    async def plugin_create_network(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        options = data.get("Options")
        net_data4 = data.get("IPv4Data")
        ipv4_data = len(net_data4) > 0 and IPv4Network(net_data4.pop().get("Pool")) or None
        net_data6 = data.get("IPv6Data")
        ipv6_data = len(net_data6) != 0 and IPv6Network(net_data6.pop().get("Pool")) or None
        log.debug(net_data4)
        log.debug(net_data6)

        for master_id, slave_id, index, n4, n6 in enumerate_networks():
            if ipv4_data == n4 or ipv6_data == n6:
                async with network_database() as ndb:
                    log.debug("{}_PEER".format(index))
                    slave = ndb.interfaces.get(ifname="blue{}".format(slave_id))
                    slave.set(ifalias=network_id)
                    slave.commit()

                    return (
                        200,
                        json.dumps(dict()),
                        [])

    async def plugin_delete_network(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")

        async with network_database() as ndb:
            vrf = ndb.interfaces.get(target="_netcrave", ifalias=network_id)
            if vrf == None:
                return (
                    200,
                    json.dumps(dict()),
                [])
            for master_id, slave_id, index, n4, n6 in enumerate_networks():
                if "blue{}".format(slave_id) == vrf.get("ifname"):
                    vrf.set(ifalias="{}_NET".format(index))
                    vrf.commit()
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
            vrf = ndb.interfaces.get(target="_netcrave", ifalias=network_id)
            slave = ndb.interfaces.get(next(vrf.ports.dump()))
            slave.set(ifalias=endpoint_id)
            slave.set(state="down")
            slave.ipaddr.clear()
            slave.commit()

            vrf.del_port(slave)
            vrf.commit()

            return (200, json.dumps({"Interface": {
                "MacAddress": slave.get("address") }}), [])

        
    async def plugin_join(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")
        sandbox_key = data.get("SandboxKey")
        options = data.get("Options")

        async with network_database() as ndb:
            slave = ndb.interfaces.get(target="_netcrave", ifalias=endpoint_id)
            for master_id, slave_id, index, n4, n6 in enumerate_networks():
                if "vif{}".format(slave_id) == slave.get("ifname"):
                    return (
                        200,
                        json.dumps(dict({
                            "InterfaceName": {
                                "SrcName": slave.get("ifname"),
                                "DstPrefix": slave.get("ifname")},
                            "Gateway": str(next(n4.hosts())),
                            "GatewayIPv6": None,
                            "StaticRoutes": []})), [])

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
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")

        async with network_database() as ndb:
            slave = ndb.interfaces.get(ifalias=endpoint_id)
            vrf = ndb.interfaces.get(ifalias=network_id)
            for master_id, slave_id, index, n4, n6 in enumerate_networks():
                if slave.get("ifname").startswith("vif{}".format(slave_id)): 
                    slave.set(ifname="vif{}".format(slave_id))
                    slave.set(ifalias="{}_PEER".format(index))
                    slave.ipaddr.clear()
                    slave.set(state="up")
                    slave.commit()

                    vrf.add_port(slave)
                    vrf.commit()

                    return (
                        200,
                        json.dumps(dict()),
                        [])

    async def plugin_leave(self, request):
        log = logging.getLogger(__name__)
        data = await handler.get_post_data(request)
        network_id = data.get("NetworkID")
        endpoint_id = data.get("EndpointID")

        async with network_database() as ndb:
            for index in Path("/srv/netcrave/_netcrave/state/netns/").iterdir():
                ndb.sources.add(netns=str(index))

            for index in ndb.interfaces.dump():
                slave = ndb.interfaces.get(index)
                if not slave.get("target").startswith("/srv/netcrave/_netcrave/state/netns/"):
                    continue
                if slave.get("ifalias") == endpoint_id:
                    slave.set(target = "_netcrave")
                    slave.commit()

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

