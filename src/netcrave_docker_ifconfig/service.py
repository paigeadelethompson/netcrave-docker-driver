from pyroute2 import IPRoute
from pyroute2 import NDB
from pyroute2 import NetNS
from netcrave_docker_ipam.scope import scope
from netcrave_docker_ipam.label import interface_type
from netcrave_docker_ipam.tags import tag


class service():
    def __init__(self):
        self._ndb = NDB()

    def ndb(self):
        return self._ndb

    def family(self, net):
        if type(IPv6Network) == type(net):
            return "inet6"
        else:
            return "inet4"

    def activate(self):
        raise NotImplementedError()

    def _create_net_namespaces(self):
        for index in get_ipam_scope_tags():
            self.ndb().sources.add(netns=index.netns_name())

    def _create_vrf_interfaces(self):
        for index in get_ipam_scope_tags():
            self.ndb().interfaces.create(
                kind='vrf',
                ifname=index.name(),
                vrf_table=index.vrf_id()).commit()

    def interface_kind(self, net):
        if interface_type.veth == net.network_interface_kind():
            return "veth"
        elif interface_type.dummy == net.network_interface_kind():
            return "dummy"
        elif interface_type.bridge == net.network_interface_kind():
            return "bridge"

    def configure_network_interfaces(self, net):
        with self.ndb().interfaces.create(
                ifname=net.network_interface_name(),
                kind=self.interface_kind(net),
                netns=net.network_namespace(),
                vrf=net.network_vrf_id()) as cur_if:
            self.configure_network_addresses(cur_if, net)

    def configure_network_addresses(self, new_if, net):
        with new_if as intf:
            intf.add_ip(str(net.network_address()),
                       prefix=net.prefix_length(),
                       family=self.family(net),
                       noprefixroute=())
            raise NotImplementedError()

    def configure_network_routes(self, net):
        raise NotImplementedError()
