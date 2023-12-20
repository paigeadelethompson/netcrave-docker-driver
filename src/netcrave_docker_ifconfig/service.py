# IAmPaigeAT (paige@paige.bio) 2023

from ipaddress import IPv6Network
from netcrave_docker_ipam.label import interface_type
from netcrave_docker_ipam.tags import get_ipam_scope_tags
from netcrave_docker_util.ndb import network_database


class service():
    async def family(self, net):
        if isinstance(IPv6Network, type(net)):
            return "inet6"
        else:
            return "inet4"

    async def activate(self):
        raise NotImplementedError()

    async def _create_net_namespaces(self):
        raise NotImplementedError()

    async def _create_vrf_interfaces(self):
        raise NotImplementedError()

    async def interface_kind(self, net):
        if interface_type.veth == net.network_interface_kind():
            return "veth"
        elif interface_type.dummy == net.network_interface_kind():
            return "dummy"
        elif interface_type.bridge == net.network_interface_kind():
            return "bridge"

    async def configure_network_interfaces(self, net):
        raise NotImplementedError()

    async def configure_network_addresses(self, new_if, net):
        raise NotImplementedError()

    async def configure_network_routes(self, net):
        raise NotImplementedError()
