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
    return NDB(db_provider = 'sqlite3', db_spec = '/srv/netcrave_netcrave/NDB/network.sqlite3')

def create_policy_routing_rules_and_routes(
    current_red, 
    current_blue, 
    current_index, 
    net_zip, 
    ndb_routes, 
    ndb_rules):
        route6 = lambda i: IPv6Network(os.environ.get("{netname}_NET_6".format(i)))
        route4 = lambda i: IPv4Network(os.environ.get("{netname}_NET_4".format(i)))
        gw6 = lambda i: next(route6(i).hosts())
        gw4 = lambda i: next(route4(i).hosts())
        yes_net6 = lambda i:  os.environ.get("{netname}_NET_6".format(i)) != None and True or False
        yes_net4 = lambda i:  os.environ.get("{netname}_NET_4".format(i)) != None and True or False
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
    db = get_NDB()
    
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
        n4 = (dotenv.get("{index}_NET_4".format(index)) != None 
                and IPv4Network(dotenv.get("{index}_NET_4".format(index))) or None)
        n6 = (dotenv.get("{index}_NET_6".format(index)) != None 
                and IPv6Network(dotenv.get("{index}_NET_6".format(index))) or None)
        a4 = (dotenv.get("{index}_IP4".format(index)) != None 
                and IPv4Address(dotenv.get("{index}_IP4".format(index))) or None)
        a6 = (dotenv.get("{index}_IP6".format(index)) != None 
                and IPv6Address(dotenv.get("{index}_IP6".format(index))) or None)

        with ndb.interfaces.create(
            target = '_netcrave', 
            kind = "vrf",
            state = 'up',
            vrf_table = red,
            ifname = "red{id}".format(red)) as vrf:
                vrf.routes.add(
                    dst = "default", 
                    table = red, 
                    metric = 4278198272, 
                    unreachable = True)
        
        with ndb.interfaces.create(
            target = '_netcrave',
            kind = "vrf",
            state = 'up',
            vrf_table = blue,
            ifname = "blue{id}".format(blue)) as vrf:
                vrf.routes.add(
                    dst = "default", 
                    table = blue, 
                    metric = 4278198272, 
                    unreachable = True)
        
        with ndb.interfaces.create(
            ifname = "vma{id}".format(red),
            kind = 'veth',
            peer = {
                'ifname': 'vsl{id}'.format(blue),
                'net_ns_fd': '_netcrave',
                'vrf_table': blue
            },
            vrf_table = red,
            net_ns_fd = "_netcrave",
            state = 'up') as network:
                if a4 != None:
                    network.add_ip(str(a4), n4.prefixlen)
                if a6 != None:
                    network.add_ip(str(a6), n6.prefixlen)
                    
        with ndb.interfaces.wait(
            target = '_netcrave', 
            ifname = "ns0sl{id}".format(blue)) as peer:  # wait for the peer
                peer.set(state = 'up')  # bring it up
                if a4 != None:
                    peer.add_ip(str(next(n4.hosts())), n4.prefixlen)
                if a6 != None:
                    peer.add_ip(str(next(n4.hosts())), n6.prefixlen)
        
        return ndb.commit()
                            
def create_configuration():
    Path.mkdir("/etc/netcrave/ssl", parents = True, exists_ok = False)
    Path.mkdir("/srv/netcrave/_netcrave/NDB", parents = True, exists_ok = True)
    
    with open("/etc/netcrave/_netcrave.json", "w") as config:
        config.write(json.dumps(netcrave_docker_config.get_default()))
    
    with open("/etc/netcrave/_netcrave.dotenv", "w") as config:
        config.write("\n".join(["{key}={value}".join(key, value) for key, value in netcrave_dotenv.get_default()]))
    
def setup_environment():
    if not Path.exists("/etc/netcrave/ssl"):
        create_configuration()
        ez_rsa().create_default_ca()
    create_networks()
