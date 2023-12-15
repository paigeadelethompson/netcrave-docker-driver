# IAmPaigeAT (paige@paige.bio) 2023

from pyroute2 import ndb
from pyroute2.ndb import events
from pyroute2.ndb.events import State
from dotenv import load_dotenv;
import os
from pathlib import Path
import netcrave_docker_dockerd.netcrave_docker_config as netcrave_docker_config
import netcrave_docker_dockerd.netcrave_dot_env as netcrave_dotenv
from netcrave_docker_dockerd.compose import get_compose
from netcrave_docker_util.crypt import ez_rsa
import json
from itertools import groupby
import re
from pyroute2 import NDB
from pyroute2 import NetNS
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from socket import AF_INET, AF_INET6 

def get_NDB():
    db = NDB(db_provider = 'sqlite3', db_spec = '/srv/netcrave/_netcrave/NDB/network.sqlite3')
    db.sources.add(netns = "_netcrave")
    with db.interfaces.wait(
        target = "_netcrave",
        ifname = "lo") as loopback:
        loopback.set(state = "up")
    return db

def create_policy_routing_rules_and_routes(
    current_red, 
    current_blue, 
    current_index, 
    ndb):
        nothing = lambda red, blue, index, ndb: []
        route6 = lambda i: IPv6Network(os.environ.get("{netname}_NET_6".format(netname = i)))
        route4 = lambda i: IPv4Network(os.environ.get("{netname}_NET_4".format(netname = i)))
        gw6 = lambda i: next(route6(i).hosts())
        gw4 = lambda i: next(route4(i).hosts())
        yes_net6 = lambda i:  os.environ.get(
            "{netname}_NET_6".format(netname = i)) != None and True or False
        yes_net4 = lambda i:  os.environ.get(
            "{netname}_NET_4".format(netname = i)) != None and True or False
        yes_route6 = lambda i1, i2: (yes_net6(i1) and yes_net6(i2))
        yes_route4 = lambda i1, i2: (yes_net4(i1) and yes_net4(i2))
        
        return (lambda func, red, blue, index, ndb: index != None 
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
                             target = "_netcrave",
                             table = blue,
                             dst = str(route6("COCKROACH")),
                             gateway = str(gw6(index)))
                         or None),
                        (yes_route4(index, "COCKROACH") 
                         and ndb.routes.create(
                             target = "_netcrave",
                             table = blue,
                             dst = str(route4("COCKROACH")),
                             gateway = str(gw4(index)))
                         or None),
                        (yes_route6(index, "COCKROACH") 
                         and ndb.rules.create(
                             target = "_netcrave",
                             table = red,
                             action = 1,
                             dst = str(route4(index).network_address),
                             dst_len = route4(index).prefixlen,
                             src = str(route4("COCKROACH").network_address),
                             src_len = route4("COCKROACH").prefixlen)
                         or None),
                        (yes_route4(index, "COCKROACH") 
                         and ndb.rules.create(
                             target = "_netcrave",
                             table = red,
                             action = 1,
                             dst = str(route6(index).network_address),
                             dst_len = route6(index).prefixlen,
                             src = str(route6("COCKROACH").network_address),
                             src_len = route6("COCKROACH").prefixlen) 
                         or None)
                        ],
                    'SQUID': nothing }.get(current_index), 
                current_red, 
                current_blue, 
                current_index,
                ndb)
                
def create_networks():
    config = netcrave_docker_config.get()
    dotenv = netcrave_dotenv.get()
    ndb = get_NDB()
    
    distinct_networks = [index for index, _ in groupby([
            index for index in dotenv.keys() 
            if index.endswith("_NET_4") 
            or index.endswith("_NET_6")], 
        key = lambda k: re.match("^[^_]+(?=_)", k).group())]
    
    net_zip = zip(
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 == 0],
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 != 0],
        distinct_networks)
    
    for red, blue, index in net_zip:
        n4 = (dotenv.get("{index}_NET_4".format(index = index)) != None 
                and IPv4Network(dotenv.get("{index}_NET_4".format(index = index))) 
                or None)
        n6 = (dotenv.get("{index}_NET_6".format(index = index)) != None 
                and IPv6Network(dotenv.get("{index}_NET_6".format(index = index)))
                or None)
        a4 = (dotenv.get("{index}_IP4".format(index = index)) != None 
                and IPv4Address(dotenv.get("{index}_IP4".format(index = index))) 
                or None)
        a6 = (dotenv.get("{index}_IP6".format(index = index)) != None 
                and IPv6Address(dotenv.get("{index}_IP6".format(index = index))) 
                or None)
        
        with ndb.interfaces.create(
            target = '_netcrave', 
            kind = "vrf",
            vrf_table = red,
            state = "up",
            ifname = "red{id}".format(id = red)) as vrf:
                with ndb.interfaces.create(
                    target = "_netcrave",
                    ifname = "vma{id}".format(id = red),
                    kind = 'veth',
                    state = "up",
                    peer = { 'ifname': 'vsl{id}'.format(id = blue), "net_ns_fd": "_netcrave" }) as veth:
                        vrf.add_port(veth)
        
        with ndb.interfaces.wait(
            target = "_netcrave",
            ifname = "red{id}".format(id = red)) as vrf:
            with ndb.interfaces.get(
                target = "_netcrave",
                ifname = "vma{id}".format(id = red)) as veth:
                    if a4 != None:
                        veth.add_ip(
                            address = str(next(n4.hosts())), 
                            prefixlen = n4.prefixlen, 
                            family = AF_INET)
                    if a6 != None:
                        veth.add_ip(
                            address = str(next(n6.hosts())), 
                            prefixlen = n6.prefixlen, 
                            family = AF_INET6)
        
        with ndb.interfaces.create(
            target = '_netcrave', 
            kind = "vrf",
            vrf_table = blue,
            state = "up",
            ifname = "blue{id}".format(id = blue)) as vrf:
                with ndb.interfaces.wait(
                    target = '_netcrave', 
                    ifname = "vsl{id}".format(id = blue)) as peer:                
                        vrf.add_port(peer)
                        peer.set(state = "up")
                        
        with ndb.interfaces.wait(
            target = "_netcrave",
            ifname = "blue{id}".format(id = blue)) as vrf:
            with ndb.interfaces.get(
                target = "_netcrave",
                ifname = "vsl{id}".format(id = blue)) as veth:
                    if a4 != None:
                        veth.add_ip(
                            address = str(a4), 
                            prefixlen = n4.prefixlen, 
                            family = AF_INET)
                    if a6 != None:
                        veth.add_ip(
                            address = str(a6),
                            prefixlen = n6.prefixlen, 
                            family = AF_INET6)
                        
        for index in create_policy_routing_rules_and_routes(red, blue, index, ndb):
            print(index)
            index.commit()
        
    return ndb
                            
def create_configuration():
    if not Path("/etc/netcrave/ssl").exists():
        Path("/etc/netcrave/ssl").mkdir(parents = True, exist_ok = False)
    
    if not Path("/srv/netcrave/_netcrave/NDB").exists():
        Path("/srv/netcrave/_netcrave/NDB").mkdir(parents = True, exist_ok = False)
    
    if not Path("/etc/netcrave/_netcrave.json").exists():
        with open("/etc/netcrave/_netcrave.json", "w") as config:
            config.write(json.dumps(netcrave_docker_config.get_default()))
    
    if not Path("/etc/netcrave/_netcrave.dotenv").exists():
        with open("/etc/netcrave/_netcrave.dotenv", "w") as config:
            config.write("\n".join(["{env_key}={env_value}".format(
                env_key = key, 
                env_value = value) for key, value in netcrave_dotenv.get_default()]))
    return

def setup_environment():
    return (
        create_configuration(),
        get_compose(),
        ez_rsa().netcrave_certificate(),
        create_networks())
