import sys, logging
from flask import Flask, request, Response
from werkzeug.serving import run_simple
import os, hashlib
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from netcrave_docker_util.exception import unknown 
from netcrave_docker_dockerd.setup_environment import get_NDB

flask_app = Flask(__name__)
headers = [("Content-Type", "application/vnd.docker.plugins.v1.2+json")]

@flask_app.errorhandler(NotImplementedError)
def handle_invalid_usage(error):
    print(request)

@flask_app.route('/Plugin.Activate',                           methods = ['POST'])
def plugin_activate():
    return (
        200, 
        json.dumps({ "Implements": ["NetworkDriver"] }), 
        headers)

@flask_app.route('/NetworkDriver.GetCapabilities',             methods = ['POST'])
def plugin_get_capabilities():
    return (
        200, 
        json.dumps({ "Scope": "local" }), 
        headers)

@flask_app.route('/NetworkDriver.CreateNetwork',               methods = ['POST'])
def plugin_create_network():
    data = json.loads(request.data)
    network_id = data.get("NetworkID")
    options = data.get("Options")
    v4 = data.get("IPv4Data")
    v6 = data.get("IPv6Data")
    
    return (
        200, 
        json.dumps(dict()), 
        headers)

@flask_app.route('/NetworkDriver.DeleteNetwork',               methods = ['POST'])
def plugin_delete_network():
    return (
        200, 
        json.dumps(dict()), 
        headers)

@flask_app.route('/NetworkDriver.CreateEndpoint',              methods = ['POST'])
def plugin_create_endpoint():
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

@flask_app.route('/NetworkDriver.Join',                        methods = ['POST'])
def plugin_join():
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

@flask_app.route('/NetworkDriver.ProgramExternalConnectivity', methods = ['POST'])
def program_external_connectivity():
    data = json.loads(request.data)
    endpoint_id = data.get("EndpointID")
    network_id = data.get("NetworkID")
    options = data.get("Options")
    return (
        200, 
        json.dumps(dict()), 
        headers)

@flask_app.route('/NetworkDriver.EndpointOperInfo',            methods = ['POST'])
def plugin_endpoint_oper_info():
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

@flask_app.route('/NetworkDriver.DeleteEndpoint',              methods = ['POST'])
def plugin_delete_endpoint():
    return (
        200, 
        json.dumps(dict()), 
        headers)

@flask_app.route('/NetworkDriver.Leave',                       methods = ['POST'])
def plugin_leave():
    return (
        200, 
        json.dumps(dict()), 
        headers)
    
@flask_app.route('/NetworkDriver.DiscoverNew',                 methods = ['POST'])
def plugin_discover_new():
    return (
        200,
        json.dumps(dict()), 
        headers)

@flask_app.route('/NetworkDriver.DiscoverDelete',              methods = ['POST'])
def plugin_discover_delete():
    return (
        200, 
        json.dumps(dict()), 
        headers)


@flask_app.route('/NetworkDriver.RevokeExternalConnectivity',  methods = ['POST'])
def revoke_external_connectivity():
    return (
        200, 
        json.dumps(dict()), 
        headers)

def oci_network_driver():
    run_simple(
        hostname     = 'unix:///run/_netcrave/docker/plugins/netcfg',
        port         = 0,
        application  = flask_app,
        use_reloader = True)


