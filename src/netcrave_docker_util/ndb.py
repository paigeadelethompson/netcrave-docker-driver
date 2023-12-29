# IAmPaigeAT (paige@paige.bio) 2023

import asyncio
from contextlib import contextmanager
import os
import logging
from pyroute2 import NDB
from singleton_decorator import singleton
from typing import ContextManager
import contextlib
import socket
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

def if_id(name, id):
    return "{name}{id}".format(name=name, id=id)

#@singleton # XXX fixme
class network_database():
    def __init__(self, *args, **kwargs):
        self._log = logging.getLogger(__name__)

        self._sem = asyncio.Lock()
        self._ndb = NDB(rtnl_debug=os.environ.get("DEBUG") and True or False)

        self._ndb.sources.add(netns="_netcrave")

    async def __aenter__(self, *args, **kwargs):
        await self._sem.acquire()
        return self._ndb

    async def __aexit__(self, *args, **kwargs):
        self._sem.release()

    @staticmethod
    def create_route(ndb, src, dst, gw, table_id, ns):
        log = logging.getLogger(__name__)
        src_addr = src != None and str(src.network_address) or None
        dst_addr = dst != None and str(dst.network_address) or None
        src_len = src != None and src.prefixlen or None
        dst_len = dst != None and dst.prefixlen or None
        gw_addr = gw != None and str(gw.network_address) or None

        if ndb.routes.exists({"target": ns, "src": src_addr, "src_len": src_len, "dst": dst_addr, "dst_len": dst_len, "gateway": gw_addr, "table": table_id}):
            log.info("route exists {src} {dst} {gw} {id} {ns}".format(src=src, dst=dst, gw=gw, id=table_id, ns=ns))
        else:
            with ndb.routes.create(
                    target=ns,
                    src=src_addr,
                    src_len=src_len,
                    dst=dst_addr,
                    dst_len=dst_len,
                    gateway=gw_addr,
                    table=table_id) as route:
                return route

    @staticmethod
    def create_rule(ndb, src, dst, action, table_id, ns):
        log = logging.getLogger(__name__)
        src_addr = src != None and str(src.network_address) or None
        dst_addr = dst != None and str(dst.network_address) or None
        src_len = src != None and src.prefixlen or None
        dst_len = dst != None and dst.prefixlen or None

        if ndb.rules.exists({"target": ns, "src": src_addr, "src_len": src_len, "dst": dst_addr, "dst_len": dst_len, "action": action, "table": table_id}):
            log.info("rule exists {src} {dst} {action} {id} {ns}".format(src=src, dst=dst, action=action, id=table_id, ns=ns))
        else:
            with ndb.rules.create(
                    target=ns,
                    table=table_id,
                    action=action,
                    src=src_addr,
                    src_len=src_len,
                    dst=dst_addr,
                    dst_len=dst.prefixlen) as rule:
                return rule

    @staticmethod
    def create_network(ndb,
                       master_interface_id,
                       slave_interface_id,
                       interface_name,
                       master_vrf_id,
                       slave_vrf_id,
                       vrf_name,
                       network_v4,
                       network_v6,
                       master_ns,
                       slave_ns,
                       master_interface_alias,
                       slave_interface_alias):
        log = logging.getLogger(__name__)
        net4 = network_v4 != None and network_v4.hosts() or None
        net6 = network_v6 != None and network_v6.hosts() or None
        net4_prefixlen = network_v4 != None and network_v4.prefixlen or None
        net6_prefixlen = network_v6 != None and network_v6.prefixlen or None

        if ndb.interfaces.exists({"target": master_ns, "ifname": if_id(interface_name, master_interface_id)}):
            log.info("interface exists {}".format(if_id(interface_name, master_interface_id)))
        else:
            with ndb.interfaces.create(
                    target=master_ns,
                    ifname=if_id(interface_name, master_interface_id),
                    kind='veth',
                    state="up",
                    peer={'ifname': if_id(interface_name, slave_interface_id), "net_ns_fd": slave_ns}) as master:
                if master_vrf_id == None:
                    if net4 != None:
                        master.add_ip(
                            address=str(next(net4)),
                            prefixlen=net4_prefixlen,
                            family=socket.AF_INET)
                    if net6 != None:
                        master.add_ip(
                            address=str(next(net6)),
                            prefixlen=net6_prefixlen,
                            family=socket.AF_INET6)
                    master.set(ifalias=master_interface_alias)
                    master.set(state="up")
            if slave_vrf_id == None:
                with ndb.interfaces.wait(
                        target=slave_ns,
                        ifname=if_id(interface_name, slave_interface_id)) as slave:
                    if net4 != None:
                        slave.add_ip(
                            address=str(next(net4)),
                            prefixlen=net4_prefixlen,
                            family=socket.AF_INET)
                    if net6 != None:
                        slave.add_ip(
                            address=str(next(net6)),
                            prefixlen=net6_prefixlen,
                            family=socket.AF_INET6)
                    slave.set(ifalias=slave_interface_alias)
                    slave.set(state="up")

        if master_vrf_id is not None and ndb.interfaces.exists({"target": master_ns, "ifname": if_id(vrf_name, master_vrf_id)}):
            log.info("interface exists {}".format(if_id(vrf_name, master_vrf_id)))
        else:
            with ndb.interfaces.create(
                    target=master_ns,
                    kind="vrf",
                    vrf_table=master_vrf_id,
                    state="up",
                    ifname=if_id(vrf_name, master_vrf_id)) as vrf:
                with ndb.interfaces.wait(
                        target=master_ns,
                        ifname=if_id(interface_name, master_interface_id)) as master:
                    vrf.add_port(master)
                    if net4 != None:
                        master.add_ip(
                            address=str(next(net4)),
                            prefixlen=net4_prefixlen,
                            family=socket.AF_INET)
                    if net6 != None:
                        master.add_ip(
                            address=str(next(net6)),
                            prefixlen=net6_prefixlen,
                            family=socket.AF_INET6)
                    master.set(ifalias=master_interface_alias)
                    master.set(state="up")

        if slave_vrf_id is not None and ndb.interfaces.exists({"target": slave_ns, "ifname": if_id(vrf_name, slave_vrf_id)}):
            log.info("interface exists {}".format(if_id(vrf_name, slave_vrf_id)))
        else:
            with ndb.interfaces.create(
                    target=slave_ns,
                    kind="vrf",
                    vrf_table=slave_vrf_id,
                    state="up",
                    ifname=if_id(vrf_name, slave_vrf_id)) as vrf:
                with ndb.interfaces.wait(
                        target=slave_ns,
                        ifname=if_id(interface_name, slave_interface_id)) as slave:
                    vrf.add_port(slave)
                    if net4 != None:
                        slave.add_ip(
                            address=str(next(net4)),
                            prefixlen=net4_prefixlen,
                            family=socket.AF_INET)
                    if net6 != None:
                        slave.add_ip(
                            address=str(next(net6)),
                            prefixlen=net6_prefixlen,
                            family=socket.AF_INET6)
                    slave.set(ifalias=slave_interface_alias)
                    slave.set(state="up")

