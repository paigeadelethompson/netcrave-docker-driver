import sys, logging
import os, hashlib
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from netcrave_docker_util.exception import unknown 
from netcrave_docker_dockerd.setup_environment import get_NDB
from aiohttp import web
import asyncio 
from netcrave_docker_util.http import serve 

class internal_driver:
    router = web.RouteTableDef()
    def __init__(self):
        self.headers = [("Content-Type", "application/vnd.docker.plugins.v1.2+json")]
        
    @router.route("POST", "/Plugin.Activate")
    async def plugin_activate(self):
        return (
            200, 
            json.dumps({ "Implements": ["NetworkDriver"] }), 
            headers)

    @router.route("POST", "/NetworkDriver.GetCapabilities")
    async def plugin_get_capabilities(self):
        return (
            200, 
            json.dumps({ "Scope": "local" }), 
            headers)

    @router.route("POST", "/NetworkDriver.CreateNetwork")
    async def plugin_create_network(self):
        data = json.loads(request.data)
        network_id = data.get("NetworkID")
        options = data.get("Options")
        v4 = data.get("IPv4Data")
        v6 = data.get("IPv6Data")
        
        return (
            200, 
            json.dumps(dict()), 
            headers)

    @router.route("POST", "/NetworkDriver.DeleteNetwork")
    async def plugin_delete_network(self):
        return (
            200, 
            json.dumps(dict()), 
            headers)
    
    @router.route("POST", "/NetworkDriver.CreateEndpoint")
    async def plugin_create_endpoint(self):
        data = json.loads(request.data)
        endpoint_id = data.get("EndpointID")
        network_id = data.get("NetworkID")
        interface = data.get("Interface")
        options = data.get("Options")
        
        sha = hashlib.sha512()
        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id = data.get("EndpointID"), 
            network_id = data.get("NetworkID")))
        
        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id = data.get("EndpointID"), 
            network_id = data.get("NetworkID")))
        
        v4 = Ipv4Network(interface.get("Address"))
        v6 = Ipv6Network(interface.get("AddressV6"))
        
        candidates = []
        
        for index in ndb.addresses.dump(): 
            current = ndb.addresses.get(index)
            if type(ip_address(current)) == IPv6Address and IPv6Address(current).is_link_local:
                    continue
            elif type(ip_address(current)) == IPv6Address:
                if IPv6Network(ip_address(current), 128).subnet_of(v6):
                    cadidates.append(index)
            elif type(ip_address(current)) == IPv4Address:
                if IPv4Network(ip_address(current), 32).subnet_of(v4):
                    cadidates.append(index)
            
        if len(set([index.get("index") for index in candidates])) != 1:
            raise unknown("requested /128 address is a subnet of more than one allocated /30 network")
        
        v4_out, v6_out = sorted(candidates, lambda index: index.get("family"))
        
        selected_index = next(tuple(candidates)).get("index")
        
        selected_interface = next((
            ndb.interfaces.get(index).get("address")
            for index in ndb.interfaces.dump()
            if ndb.interfaces.get(index).get("ifname") == selected_interface.get("label")))   
        
        selected_interface.set("ifalias", sha.hexdigest())
        selected.interface.commit()

        return (
            200, 
            json.dumps({
                "Interface": 
                    { 
                        "Address": str(IPv4Address(v4_out)),
                        "AddressV6": str(IPv6Address(v6_out)),
                        "MacAddress": selected_interface.get("address"),
                    }
                }), 
            headers)
                    
    
    @router.route("POST", "/NetworkDriver.Join")
    async def plugin_join(self):
        data = json.loads(request.data)
        endpoint_id = data.get("EndpointID")
        network_id = data.get("NetworkID")
        sandbox_key = data.get("SandboxKey")
        options = data.get("Options")
        
        return (
            200, 
            json.dumps(json.dumps({
                'InterfaceName': {
                    'SrcName': None,
                    'DstPrefix': 'eth',
                    'Gateway': None }}), 
                    headers))
                
    
    @router.route("POST", "/NetworkDriver.ProgramExternalConnectivity")
    async def plugin_program_external_connectivity(self):
        data = json.loads(request.data)
        endpoint_id = data.get("EndpointID")
        network_id = data.get("NetworkID")
        options = data.get("Options")
        return (
            200, 
            json.dumps(dict()), 
            headers)

    
    @router.route("POST", "/NetworkDriver.EndpointOperInfo")
    async def plugin_endpoint_oper_info(self):
        data = json.loads(request.data)
        endpoint_id = data.get("EndpointID")
        network_id = data.get("NetworkID")
        
        sha.update("{endpoint_id}{network_id}".format(
            endpoint_id = data.get("EndpointID"), 
            network_id = data.get("NetworkID")))
        
        oper = next((ndb.interfaces.get(index) 
                    for index in ndb.interfaces.dump() 
                    if index["iflias"] == sha.hexdigest()))
        
        net = next((ndb.addresses.get(index) 
            for index in ndb.addresses.dump() 
            if ndb.addresses.get(index).get("label") == oper.get("ifname")))
        
        network = Ipv4Network(
            "{addr}/32".format(
                addr = net.get(
                    "address"))).supernet(
                        new_prefix = net.get("prefixlen"))
        
        return (
            200, 
            json.dumps({
                "Value": {
                endpoint_id: oper.get("ifname"),
                network_id: str(network)}}), 
            headers)

    @router.route("POST", "/NetworkDriver.DeleteEndpoint")
    async def plugin_delete_endpoint(self):
        return (
            200, 
            json.dumps(dict()), 
            headers)

    @router.route("POST", "/NetworkDriver.Leave")
    async def plugin_leave(self):
        return (
            200, 
            json.dumps(dict()), 
            headers)
    
    @router.route("POST", "/NetworkDriver.DiscoverNew")
    async def plugin_discover_new(self):
        return (
            200,
            json.dumps(dict()), 
            headers)
    
    @router.route("POST", "/NetworkDriver.DiscoverDelete")
    async def plugin_discover_delete(self):
        return (
            200, 
            json.dumps(dict()), 
            headers)
    
    @router.route("POST", "/NetworkDriver.RevokeExternalConnectivity")
    async def plugin_revoke_external_connectivity(self):
        return (
            200, 
            json.dumps(dict()), 
            headers)

async def internal_network_driver():
    await serve(
        internal_driver, 
        unix_socket = "/run/_netcrave/docker/plugins/netcfg")
