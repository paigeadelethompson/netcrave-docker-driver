# IAmPaigeAT (paige@paige.bio) 2023
from pyroute2 import ndb
from pyroute2.ndb import events
from pyroute2.ndb.events import State
from dotenv import load_dotenv
import os
from pathlib import Path
import netcrave_docker_dockerd.netcrave_docker_config as netcrave_docker_config
import netcrave_docker_dockerd.netcrave_dot_env as netcrave_dotenv
from netcrave_docker_util.lazy import swallow
from netcrave_docker_util.exception import unknown
from netcrave_docker_dockerd.compose import get_compose
from netcrave_docker_util.ca import ez_rsa
import json
from itertools import groupby
import re
from pyroute2 import NDB
from pyroute2 import NetNS
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from socket import AF_INET, AF_INET6
from pwd import getpwnam
import logging
from netcrave_docker_util.cmd import cmd_async
import aiofiles


async def get_NDB():
    db = NDB(
        db_provider='sqlite3',
        db_spec='/srv/netcrave/_netcrave/NDB/network.sqlite3',
        rtnl_debug=os.environ.get("DEBUG") and True or False,
        log="off")
    return db


async def create_policy_routing_rules_and_routes(
        current_red,
        current_blue,
        current_index,
        ndb):
    def nothing(red, blue, index, ndb): return []

    def route6(i): return IPv6Network(
        os.environ.get(
            "{netname}_NET_6".format(
                netname=i)))

    def route4(i): return IPv4Network(
        os.environ.get(
            "{netname}_NET_4".format(
                netname=i)))

    def gw6(i): return next(route6(i).hosts())
    def gw4(i): return next(route4(i).hosts())

    def yes_net6(i): return os.environ.get(
        "{netname}_NET_6".format(netname=i)) is not None and True or False
    def yes_net4(i): return os.environ.get(
        "{netname}_NET_4".format(netname=i)) is not None and True or False

    def yes_route6(i1, i2): return (yes_net6(i1) and yes_net6(i2))
    def yes_route4(i1, i2): return (yes_net4(i1) and yes_net4(i2))

    return (lambda func, red, blue, index, ndb: index is not None
            and func(red, blue, index, ndb)
            or ())({
                'IPAM': nothing,
                'IFCONFIG': nothing,
                'ICAP': nothing,
                'HAPROXYCFG': nothing,
                'HAPROXY': nothing,
                'FLUENTD': nothing,
                'DNSD': nothing,
                'DAVFS': nothing,
                'COCKROACH': nothing,
                'CERTIFICATEMGR': nothing,
                'ACME': nothing,
                'POWERDNS': lambda red, blue, index, ndb: [
                    (yes_route6(index, "COCKROACH")
                     and ndb.routes.create(
                         target="_netcrave",
                         table=blue,
                         dst=str(route6("COCKROACH")),
                         gateway=str(gw6(index)))
                     or None),
                    (yes_route4(index, "COCKROACH")
                     and ndb.routes.create(
                         target="_netcrave",
                         table=blue,
                         dst=str(route4("COCKROACH")),
                         gateway=str(gw4(index)))
                     or None),
                    (yes_route6(index, "COCKROACH")
                     and ndb.rules.create(
                         target="_netcrave",
                         table=red,
                         action=1,
                         dst=str(route4(index).network_address),
                         dst_len=route4(index).prefixlen,
                         src=str(route4("COCKROACH").network_address),
                         src_len=route4("COCKROACH").prefixlen)
                     or None),
                    (yes_route4(index, "COCKROACH")
                     and ndb.rules.create(
                         target="_netcrave",
                         table=red,
                         action=1,
                         dst=str(route6(index).network_address),
                         dst_len=route6(index).prefixlen,
                         src=str(route6("COCKROACH").network_address),
                         src_len=route6("COCKROACH").prefixlen)
                     or None)
                ],
                'SQUID': nothing}.get(current_index),
        current_red,
        current_blue,
        current_index,
        ndb)


async def create_networks():
    log = logging.getLogger(__name__)
    dotenv = netcrave_dotenv.get()
    ndb = await get_NDB()

    if ndb.netns.exists("_netcrave"):
        log.info("networking already configured, not re-creating")
        return ndb

    log.debug(ndb.sources.add(netns="_netcrave"))

    with ndb.interfaces.wait(target="_netcrave", ifname="lo") as loopback:
        log.debug(loopback.set(state="up"))

    distinct_networks = [index for index, _ in groupby([
        index for index in dotenv.keys()
        if index.endswith("_NET_4")
        or index.endswith("_NET_6")],
        key=lambda k: re.match("^[^_]+(?=_)", k).group())]

    net_zip = zip(
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 == 0],
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 != 0],
        distinct_networks)

    log.debug(net_zip)

    for red, blue, index in net_zip:
        n4 = (dotenv.get("{index}_NET_4".format(index=index)) is not None
              and IPv4Network(dotenv.get("{index}_NET_4".format(index=index)))
              or None)
        n6 = (dotenv.get("{index}_NET_6".format(index=index)) is not None
              and IPv6Network(dotenv.get("{index}_NET_6".format(index=index)))
              or None)
        a4 = (dotenv.get("{index}_IP4".format(index=index)) is not None
              and IPv4Address(dotenv.get("{index}_IP4".format(index=index)))
              or None)
        a6 = (dotenv.get("{index}_IP6".format(index=index)) is not None
              and IPv6Address(dotenv.get("{index}_IP6".format(index=index)))
              or None)

        with ndb.interfaces.create(
                target='_netcrave',
                kind="vrf",
                vrf_table=red,
                state="up",
                ifname="red{id}".format(id=red)) as vrf:
            with ndb.interfaces.create(
                    target="_netcrave",
                    ifname="vma{id}".format(id=red),
                    kind='veth',
                    state="up",
                    peer={'ifname': 'vsl{id}'.format(id=blue), "net_ns_fd": "_netcrave"}) as veth:
                vrf.add_port(veth)
                log.debug("A Master interface in RED plane {}".format(veth))
                log.debug(
                    "A VRF in RED plane, master interface assigned {}".format(vrf))

        with ndb.interfaces.wait(
                target="_netcrave",
                ifname="red{id}".format(id=red)) as vrf:
            with ndb.interfaces.get(
                    target="_netcrave",
                    ifname="vma{id}".format(id=red)) as veth:
                if a4 is not None:
                    veth.add_ip(
                        address=str(next(n4.hosts())),
                        prefixlen=n4.prefixlen,
                        family=AF_INET)
                if a6 is not None:
                    veth.add_ip(
                        address=str(next(n6.hosts())),
                        prefixlen=n6.prefixlen,
                        family=AF_INET6)
                log.debug(
                    "Assign addresses to a master interface in the RED plane".format(veth))
                log.debug(
                    "RED VRF should be unchanged, but required dependency to VETH address assignment".format(vrf))

        with ndb.interfaces.create(
                target='_netcrave',
                kind="vrf",
                vrf_table=blue,
                state="up",
                ifname="blue{id}".format(id=blue)) as vrf:
            with ndb.interfaces.wait(
                    target='_netcrave',
                    ifname="vsl{id}".format(id=blue)) as peer:
                vrf.add_port(peer)
                peer.set(state="up")
                log.debug("A slave interface in BLUE plane {}".format(peer))
                log.debug(
                    "A VRF in BLUE plane, slave interface assigned {}".format(vrf))

        with ndb.interfaces.wait(
                target="_netcrave",
                ifname="blue{id}".format(id=blue)) as vrf:
            with ndb.interfaces.get(
                    target="_netcrave",
                    ifname="vsl{id}".format(id=blue)) as veth:
                if a4 is not None:
                    veth.add_ip(
                        address=str(a4),
                        prefixlen=n4.prefixlen,
                        family=AF_INET)
                if a6 is not None:
                    veth.add_ip(
                        address=str(a6),
                        prefixlen=n6.prefixlen,
                        family=AF_INET6)
                log.debug(
                    "Assign addresses to a slave interface in the BLUE plane".format(veth))
                log.debug(
                    "BLUE VRF should be unchanged, but required dependency to VETH address assignment".format(vrf))

        for index in await create_policy_routing_rules_and_routes(red, blue, index, ndb):
            log.debug("commiting route/rule to NDB {}".format(index.commit()))
    return ndb


async def create_configuration():
    if not swallow(lambda: getpwnam("_netcrave")):
        await cmd_async("/usr/bin/env", "groupadd", "_netcrave")

    Path("/run/netcrave/_netcrave").mkdir(parents=True, exist_ok=True)
    Path("/run/netcrave/_netcrave/sock.dockerd").unlink(missing_ok=True)
    Path("/run/netcrave/_netcrave/sock.containerd").unlink(missing_ok=True)
    Path("/srv/netcrave/_netcrave/state/plugins").mkdir(parents=True, exist_ok=True)
    Path("/srv/netcrave/_netcrave/data").mkdir(parents=True, exist_ok=True)
    Path("/srv/netcrave/_netcrave/containerd").mkdir(parents=True, exist_ok=True)
    Path("/srv/netcrave/_netcrave/NDB").mkdir(parents=True, exist_ok=True)
    Path("/etc/netcrave/ssl").mkdir(parents=True, exist_ok=True)

    if not Path("/etc/netcrave/_netcrave.json").exists():
        async with aiofiles.open("/etc/netcrave/_netcrave.json", "w") as config:
            await config.write(json.dumps(netcrave_docker_config.get_default()))

    if not Path("/etc/netcrave/_netcrave.dotenv").exists():
        async with aiofiles.open("/etc/netcrave/_netcrave.dotenv", "w") as config:
            await config.write("\n".join(["{env_key}={env_value}".format(
                env_key=key,
                env_value=value) for key, value in netcrave_dotenv.get_default()]))


async def setup_compose():
    return await get_compose()


async def setup_environment():
    await create_configuration()
    ca = await ez_rsa().netcrave_certificate()
    ndb = await create_networks()
    return (ca, ndb)
