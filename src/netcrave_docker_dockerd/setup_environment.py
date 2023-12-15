from pyroute2 import ndb
from pyroute2.ndb import events
from pyroute2.ndb.events import State
from dotenv import load_dotenv;
import os
from pathlib import Path
import netcrave_docker_dockerd.netcrave_docker_config as netcrave_docker_config
import netcrave_docker_dockerd.netcrave_dot_env as netcrave_dotenv
from netcrave_docker_util.crypt import ez_rsa
import json
from itertools import groupby
import re
from pyroute2 import NDB
from pyroute2 import NetNS
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network

def get_NDB():
    return NDB(db_provider = 'sqlite3', db_spec = '/srv/netcrave/_netcrave/NDB/network.sqlite3')

def create_policy_routing_rules_and_routes(
    current_red, 
    current_blue, 
    current_index, 
    net_zip, 
    ndb_routes, 
    ndb_rules):
        route6 = lambda i: IPv6Network(os.environ.get("{netname}_NET_6".format(netname = i)))
        route4 = lambda i: IPv4Network(os.environ.get("{netname}_NET_4".format(netname = i)))
        gw6 = lambda i: next(route6(i).hosts())
        gw4 = lambda i: next(route4(i).hosts())
        yes_net6 = lambda i:  os.environ.get("{netname}_NET_6".format(netname = i)) != None and True or False
        yes_net4 = lambda i:  os.environ.get("{netname}_NET_4".format(netname = i)) != None and True or False
        yes_route6 = lambda i1, i2: (yes_net6(i1) and yes_net6(i2))
        yes_route4 = lambda i1, i2: (yes_net4(i1) and yes_net4(i2))
        
        return (lambda r, b, i, z, ro, ru, f: i != None and f(r, b, i, z, ro, ru) 
            or ())({
                'IPAM': lambda r, b, i, z, ro, ru: True,
                'IFCONFIG': lambda r, b, i, z, ro, ru: True,
                'ICAP': lambda r, b, i, z, ro, ru: True,
                'HAPROXYCFG': lambda r, b, i, z, ro, ru: True,
                'HAPROXY': lambda r, b, i, z, ro, ru: True,
                'FLUENTD': lambda r, b, i, z, ro, ru: True,
                'DNSD': lambda r, b, i, z, ro, ru: True,
                'DAVFS': lambda r, b, i, z, ro, ru: True,
                'COCKROACH': lambda r, b, i, z, ro, ru: True,
                'CERTIFICATEMGR': lambda r, b, i, z, ro, ru: True,
                'ACME': lambda r, b, i, z, ro, ru: True,
                'POWERDNS': lambda r, b, i, z, ro, ru: [
                    (yes_route6(i, "COCKROACH") and ro.add(
                        table = b,
                        dst = route6("COCKROACH"),
                        gateway = gw6(i)) or None),
                    (yes_route4(i, "COCKROACH") and ro.add(
                        table = b,
                        dst = route4("COCKROACH"),
                        gateway = gw4(i)) or None),
                    (yes_route6(i, "COCKROACH") and ru.add(
                        table = r,
                        dst = route6(i),
                        src = route6("COCKROACH")) or None),
                    (yes_route4(i, "COCKROACH") and ru.add(
                        table = r,
                        dst = route4(i),
                        src = route4("COCKROACH")) or None)
                    ],
                'SQUID': lambda r, b, i, z, ro, ru: True }.get(current_index), 
            current_red, 
            current_blue, 
            current_index, 
            net_zip, 
            ndb_routes, 
            ndb_rules)
    
def create_networks():
    config = netcrave_docker_config.get()
    dotenv = netcrave_dotenv.get()
    ndb = get_NDB()
    
    distinct_networks = [index for index, _ in groupby([
            index for index in dotenv.keys() 
            if index.endswith("_NET_4") 
            or index.endswith("_NET_6")], 
        key = lambda k: re.match("^[^_]+(?=_)", k).group())]
    
    ndb.sources.add(netns = "_netcrave")
    
    net_zip = zip(
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 == 0],
        [index for index in range(1, (len(distinct_networks) * 2)) if index % 2 != 0],
        distinct_networks)
    
    for red, blue, index in net_zip:
        n4 = (dotenv.get("{index}_NET_4".format(index = index)) != None 
                and IPv4Network(dotenv.get("{index}_NET_4".format(index = index))) or None)
        n6 = (dotenv.get("{index}_NET_6".format(index = index)) != None 
                and IPv6Network(dotenv.get("{index}_NET_6".format(index = index))) or None)
        a4 = (dotenv.get("{index}_IP4".format(index = index)) != None 
                and IPv4Address(dotenv.get("{index}_IP4".format(index = index))) or None)
        a6 = (dotenv.get("{index}_IP6".format(index = index)) != None 
                and IPv6Address(dotenv.get("{index}_IP6".format(index = index))) or None)
        
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
                    peer = { 'ifname': 'vsl{id}'.format(id = blue), "net_ns_fd": "_netcrave", "state": "up"}) as veth:
                        vrf.add_port(veth)
                        if a4 != None:
                            veth.add_ip("{address}/{prefixlen}".format(address = str(a4), prefixlen = n4.prefixlen))
                        if a6 != None:
                            veth.add_ip("{address}/{prefixlen}".format(address = str(a6), prefixlen = n6.prefixlen))
                            
        
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
                        if a4 != None:
                            peer.add_ip("{address}/{prefixlen}".format(
                                address = str(next(n4.hosts())), 
                                prefixlen = n4.prefixlen))                
                        if a6 != None:
                            peer.add_ip("{address}/{prefixlen}".format(
                                address = str(next(n6.hosts())), 
                                prefixlen = n6.prefixlen))
        return ndb
                            
def create_configuration():
    Path("/etc/netcrave/ssl").mkdir(parents = True, exist_ok = False)
    Path("/srv/netcrave/_netcrave/NDB").mkdir(parents = True, exist_ok = True)
    
    with open("/etc/netcrave/_netcrave.json", "w") as config:
        config.write(json.dumps(netcrave_docker_config.get_default()))
    
    with open("/etc/netcrave/_netcrave.dotenv", "w") as config:
        config.write("\n".join(["{env_key}={env_value}".format(
            env_key = key, 
            env_value = value) for key, value in netcrave_dotenv.get_default()]))
    
def setup_environment():
    if not Path("/etc/netcrave/ssl").exists():
        create_configuration()
        ez_rsa().create_default_ca()
    create_networks()
