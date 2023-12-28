# IAmPaigeAT (paige@paige.bio) 2023

import os
from pathlib import Path
import shutil
import json
from itertools import groupby
import re
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from socket import AF_INET, AF_INET6
import logging
import aiofiles
from typing import Callable
import netcrave_docker_dockerd.netcrave_docker_config as netcrave_docker_config
import netcrave_docker_dockerd.netcrave_dot_env as netcrave_dotenv
from pyroute2.netns import setns
from pyroute2.nftables.main import NFTables
from netcrave_docker_util.cmd import cmd_async
from netcrave_docker_util.ca import ez_rsa
from netcrave_docker_util.ndb import network_database
from netcrave_docker_dockerd.compose import get_compose

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

async def create_policy_routing_rules_and_routes(current_index) -> Callable[[int, int, str, object], list]:
    map = {
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
             or nothing),
            (yes_route4(index, "COCKROACH")
             and ndb.routes.create(
                 target="_netcrave",
                 table=blue,
                 dst=str(route4("COCKROACH")),
                 gateway=str(gw4(index)))
             or nothing),
            (yes_route6(index, "COCKROACH")
             and ndb.rules.create(
                 target="_netcrave",
                 table=red,
                 action=1,
                 dst=str(route4(index).network_address),
                 dst_len=route4(index).prefixlen,
                 src=str(route4("COCKROACH").network_address),
                 src_len=route4("COCKROACH").prefixlen)
             or nothing),
            (yes_route4(index, "COCKROACH")
             and ndb.rules.create(
                 target="_netcrave",
                 table=red,
                 action=1,
                 dst=str(route6(index).network_address),
                 dst_len=route6(index).prefixlen,
                 src=str(route6("COCKROACH").network_address),
                 src_len=route6("COCKROACH").prefixlen)
             or nothing)
        ],
        'SQUID': nothing
    }

    return map.get(current_index) or nothing

async def create_internet_gateway(green, ndb, slave_ns):
    log = logging.getLogger(__name__)
    try:
        with ndb.interfaces.create(
                kind="vrf",
                vrf_table=green,
                state="up",
                ifname="green{id}".format(id=green)) as vrf:
            with ndb.interfaces.create(
                    ifname="igwma{id}".format(id=green),
                    kind='veth',
                    state="up",
                    peer={'ifname': 'igwsl{id}'.format(id=green), "net_ns_fd": slave_ns}) as veth:
                vrf.add_port(veth)
                veth.add_ip(
                    address=str("10.254.0.1"),
                    prefixlen=30,
                    family=AF_INET)
                log.debug("A Master interface in GREEN plane {}".format(veth))
                log.debug("A VRF in GREEN plane, master interface assigned {}".format(vrf))

        with ndb.interfaces.wait(
                target=slave_ns,
                ifname="igwsl{id}".format(id=green)) as peer:
            peer.add_ip(
                address=str("10.254.0.2"),
                prefixlen=30,
                family=AF_INET)
            peer.set(state="up")
            log.debug("primary gateway slave interface assigned to ns {}".format(slave_ns))
    except:
        log.debug("IGW may already exist")

async def create_networks():
    """Creates netowrks; VRFs, interfaces, routes and routing rules
    for the *internal* networking driver, see also the external
    networking driver. This driver primarily handles networking
    for the driver stack to function.

    Inside of each NetNS compartment there are two VRF planes, RED and BLUE,
    RED and BLUE both refer to multiple VRFs.

    RED VRFs refer to routes in and out of the NetNS from the container host
    BLUE VRFs refer to routes between the container host and container

    For example, in the _netcrave NetNS, a red VRF can share an interface with
    another RED VRF in another namespace. Route rules can be created to allow
    traffic from BLUE VRFs into those routes.

    :returns: None

    """

    log = logging.getLogger(__name__)
    dotenv = netcrave_dotenv.get()
    async with network_database() as ndb:
        try:
            await create_internet_gateway(127, ndb, "_netcrave")

            with ndb.interfaces.wait(target="_netcrave", ifname="lo") as loopback:
                log.debug(loopback.set(state="up"))

            distinct_networks = [index for index, _ in groupby([
                index for index in dotenv.keys()
                if index.endswith("_NET_4")
                or index.endswith("_NET_6")],
                key=lambda k: re.match("^[^_]+(?=_)", k).group())]

            net_zip = zip(
                [index for index in range(128, 128 + (len(distinct_networks) * 2)) if index % 2 == 0],
                [index for index in range(128, 128 + (len(distinct_networks) * 2)) if index % 2 != 0],
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
        except:
            pass
        try:
                with ndb.interfaces.wait(
                        target="_netcrave",
                        ifname="red{id}".format(id=red)) as vrf:
                    with ndb.interfaces.get(
                            target="_netcrave",
                            ifname="vma{id}".format(id=red)) as veth:
                        if a4 is not None and n4 is not None:
                            veth.add_ip(
                                address=str(next(n4.hosts())),
                                prefixlen=n4.prefixlen,
                                family=AF_INET)
                        if a6 is not None and n6 is not None:
                            veth.add_ip(
                                address=str(next(n6.hosts())),
                                prefixlen=n6.prefixlen,
                                family=AF_INET6)
                        log.debug(
                            "Assign addresses to a master interface in the RED plane".format(veth))
                        log.debug(
                            "RED VRF should be unchanged, but required dependency to VETH address assignment".format(
                                vrf))
        except:
            pass
        try:
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
                        log.debug("A VRF in BLUE plane, slave interface assigned {}".format(vrf))

                with ndb.interfaces.wait(
                        target="_netcrave",
                        ifname="blue{id}".format(id=blue)) as vrf:
                    with ndb.interfaces.get(
                            target="_netcrave",
                            ifname="vsl{id}".format(id=blue)) as veth:
                        if a4 is not None and n4 is not None:
                            veth.add_ip(
                                address=str(a4),
                                prefixlen=n4.prefixlen,
                                family=AF_INET)
                        if a6 is not None and n6 is not None:
                            veth.add_ip(
                                address=str(a6),
                                prefixlen=n6.prefixlen,
                                family=AF_INET6)
                        log.debug("Assign addresses to a slave interface in the BLUE plane".format(veth))
                        log.debug("BLUE VRF should be unchanged, but required dependency to VETH address assignment".format(
                                vrf))
        except:
            log.warn("NDB may already be initialized...")

        rows = await create_policy_routing_rules_and_routes(index)
        for row in rows(red, blue, index, ndb):
            try:
                log.debug("commiting route/rule to NDB {}".format(row.commit()))
            except:
                log.warn("failed to add route, may already exist")

async def get_id(user_name, which="/etc/passwd"):
    async with aiofiles.open(which) as users:
        return int([int(index.split(":").pop(2))
         for index in await users.readlines()
         if index.split(":").pop(0) == user_name].pop())

async def create_users_and_groups(names = ["_netcrave"]):
    log = logging.getLogger(__name__)

    for name in names:
        result_gid = await cmd_async("id", "-g", name)
        result_uid = await cmd_async("id", "-u", name)

        if result_gid != 0 or result_uid != 0:
            log.debug("creating user and group {}".format(name))

            async with aiofiles.open("/etc/passwd") as users:
                free_uids = set.difference(
                    set(range(0, 65534)),
                    set(sorted([int(index.split(":").pop(2))
                                for index in await users.readlines()])))

                async with aiofiles.open("/etc/group") as groups:
                    free_gids = set.difference(
                        set(range(0, 65534)),
                        set(sorted([int(index.split(":").pop(2))
                                    for index in await groups.readlines()])))

                    id = free_uids.intersection(free_gids).pop()

                    result = await cmd_async("groupadd", "-g", id, "-r", name)
                    if result != 0:
                        raise Exception("error creating group {}".format(name))

                    result = await cmd_async("useradd", "-g", id, "-u", id, "-r", name)
                    if result != 0:
                        raise Exception("error creating user {}".format(name))

async def create_configuration():
    """Creates configuration files and directories

    :returns: None

    """
    if not Path("/opt/netcrave").exists():
        raise Exception("runtime executables need to be installed first")

    Path("/run/netcrave/_netcrave").mkdir(parents=True, exist_ok=True)
    Path("/run/netcrave/_netcrave/sock.dockerd").unlink(missing_ok=True)
    Path("/run/netcrave/_netcrave/sock.containerd").unlink(missing_ok=True)
    Path("/srv/netcrave/_netcrave/state/plugins").mkdir(parents=True, exist_ok=True)

    Path("/run/docker/plugins").mkdir(parents=True, exist_ok=True)
    shutil.chown(Path("/run/docker/plugins"), group = "_netcrave")
    Path("/run/docker/plugins").chmod(0o770)

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


async def change_netns(net_ns = "_netcrave"):
    """Mounts enabled cgroups to NetNS

    :param net_ns: the network namespace to work in
    :returns: None

    """

    # try:
    log = logging.getLogger(__name__)
    setns(net_ns)

async def restore_default_netns():
    setns("/proc/1/ns/net")


async def setup_environment():
    """Calls all initialization functions

    :returns: None

    """
    await create_users_and_groups()
    await create_configuration()
    _ = await ez_rsa().netcrave_certificate()
    await create_networks()
