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
import nftables
import netcrave_docker_dockerd.netcrave_docker_config as netcrave_docker_config
import netcrave_docker_dockerd.netcrave_dot_env as netcrave_dotenv
from pyroute2.netns import setns
from pyroute2.nftables.main import NFTables
from netcrave_docker_util.cmd import cmd_async
from netcrave_docker_util.ca import ez_rsa
from netcrave_docker_util.ndb import network_database
from netcrave_docker_dockerd.compose import get_compose
from netcrave_docker_util.nft import nft_nat4_rules


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

async def create_internet_gateway(ndb):
    log = logging.getLogger(__name__)
    try:
        network_database.create_network(ndb=ndb,
                                        master_interface_id=127,
                                        slave_interface_id=127,
                                        interface_name="igw",
                                        master_vrf_id=127,
                                        slave_vrf_id=None,
                                        vrf_name="green",
                                        network_v4=IPv4Network("192.0.2.0/30"),
                                        network_v6=None,
                                        master_ns=None,
                                        slave_ns="_netcrave",
                                        master_interface_alias="NETCRAVE_IGW_MASTER",
                                        slave_interface_alias="NETCRAVE_IGW_SLAVE")

        network_database.create_route(ndb=ndb,
                                      src=None,
                                      dst=IPv4Network("0.0.0.0/0"),
                                      gw=IPv4Network("192.0.2.2/32"),
                                      table_id=None,
                                      ns="_netcrave")

        network_database.create_rule(ndb=ndb,
                                     src=None,
                                     dst=IPv4Network("192.0.2.0/30"),
                                     action=1,
                                     table_id=127,
                                     ns=None)
        nft = nftables.Nftables()

        if not nft.json_validate(nft_nat4_rules()):
            raise Exception("nat4 rules validation")

        
        _, _, _ = nft.cmd("flush table inet _netcrave")
        _, _, _ = nft.cmd("delete set inet _netcrave masquerade_networks4")

        rc, output, error = nft.json_cmd(nft_nat4_rules())
        if rc != 0:
            raise Exception("{} {}, {}".format(rc, output, error))
        
        cmd = "add element inet _netcrave masquerade_networks4 { " + str(ndb.routes.get(dst="default").get("oif")) + ". 192.0.2.0/30 : jump masq }"

        rc, output, error = nft.cmd(cmd)
        if rc != 0:
            raise Exception("{} {}, {}".format(rc, output, error))
        
    except Exception as ex:
        log.critical(ex)
        raise

async def create_networks():
    log = logging.getLogger(__name__)
    dotenv = netcrave_dotenv.get()

    async with network_database() as ndb:
        try:
            await create_internet_gateway(ndb)

            with ndb.interfaces.wait(target="_netcrave", ifname="lo") as loopback:
                loopback.set(state="up")

            distinct_networks = [index for index, _ in groupby([
                index for index in dotenv.keys()
                if index.endswith("_NET_4")
                or index.endswith("_NET_6")],
                key=lambda k: re.match("^[^_]+(?=_)", k).group())]

            net_zip = zip(
                [index for index in range(128, 128 + (len(distinct_networks) * 2)) if index % 2 == 0],
                [index for index in range(128, 128 + (len(distinct_networks) * 2)) if index % 2 != 0],
                distinct_networks)

            for master_id, slave_id, index in net_zip:
                n4 = (dotenv.get("{index}_NET_4".format(index=index)) is not None
                    and IPv4Network(dotenv.get("{index}_NET_4".format(index=index)))
                    or None)

                n6 = (dotenv.get("{index}_NET_6".format(index=index)) is not None
                    and IPv6Network(dotenv.get("{index}_NET_6".format(index=index)))
                    or None)

                network_database.create_network(ndb=ndb,
                                                master_interface_id=master_id,
                                                slave_interface_id=slave_id,
                                                interface_name="vif",
                                                master_vrf_id=master_id,
                                                slave_vrf_id=slave_id,
                                                vrf_name="blue",
                                                network_v4=n4,
                                                network_v6=n6,
                                                master_ns="_netcrave",
                                                slave_ns="_netcrave",
                                                master_interface_alias="{name}_GATEWAY".format(name=index),
                                                slave_interface_alias="{name}_PEER".format(name=index))

        except Exception as ex:
            log.critical(ex)
            raise

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
