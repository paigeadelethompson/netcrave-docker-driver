from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, ip_address
import uuid
from collections import deque
from netcrave_docker_ipam.scope import scope

def get_network_object(network, prefix_length):
    net = ip_address(network)
    if type(net) == IPv4Address:
        return IPv4Network(net).supernet(new_prefix = prefix_length)
    elif type(net) == IPv6Address:
        return IPv6Network(net).supernet(new_prefix = prefix_length)

def network_object_to_uuid(network):
    if type(network) == IPv4Network:
        return uuid.UUID(bytes = bytes([0x00] * 12) + network.network_address.packed)
    elif type(network) == IPv6Network:
        return uuid.UUID(bytes = network.network_address.packed)

def uuid_to_address_object(id):
    if int.from_bytes(id.bytes[:12]) == 0:
        return IPv4Address(int.from_bytes(id.bytes[12:16]))
    else:
        return IPv6Address(int.from_bytes(id.bytes))

def get_ipv6_network_object_from_token(parent, token, prefix_len):
    net_bytes = [index for index in parent.network_address.packed[::-1] if index != 0][::-1]
    token_bytes = [index for index in token.network_address.packed if index != 0]
    zeroes = 16 - len(net_bytes + token_bytes)
    return IPv6Network(IPv6Address(int.from_bytes(bytes(net_bytes) + bytes(token_bytes) + bytes([0] * zeroes)))).supernet(new_prefix = prefix_len)

class schema():
    _default_schema = {
        'reserved_vrf_ids': [1],
        'schema_version': 2,
        'templates': [{
            'name': 'default',
            'scopes': [{
                'ipv4_prefix_length': 24,
                'ipv4_allocation_length': [32],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [127]
            }, {
                'ipv4_prefix_length': 24,
                'ipv4_allocation_length': [31],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [127]
            }, {
                'ipv4_prefix_length': 24,
                'ipv4_allocation_length': [30],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [125]
            }, {
                'ipv4_prefix_length': 24,
                'ipv4_allocation_length': [29],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [124]
            }, {
                'ipv4_prefix_length': 24,
                'ipv4_allocation_length': [28],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [123]
            }, {
                'ipv4_prefix': 24,
                'ipv4_allocation_length': [27],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [122]
            }, {
                'ipv4_prefix': 24,
                'ipv4_allocation_length': [26],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [121]
            }, {
                'ipv4_prefix': 24,
                'ipv4_allocation_length': [25],
                'ipv6_prefix_length': 120,
                'ipv6_allocation_length': [120]
            }, {
                'ipv4_prefix': 21,
                'ipv4_allocation_length': [22, 23, 24],
                'ipv6_prefix_length': 117,
                'ipv6_allocation_length': [118]
            }]}],
        'scopes': [{
            'ipv4_network': '10.0.0.0',
            'ipv4_prefix_length': 16,
            'vrf_id': 2,
            'ipv6_network': ['fc00:ffff:ffff:ffff::'],
            'ipv6_prefix_length': 64,
            'tags': ['docker-local'],
            'scopes': [{
                'ipv4_network': '10.0.0.0',
                'ipv4_prefix_length': 20,
                'tags': ['default-container-network'],
                'egress': ['cluster-local-ingress', 'docker-local-ingress', 'internet'],
                'ingress': ['cluster-local-egress', 'docker-local-egress'],
                'ipv6_network': '::ff10:fff0:fff0',
                'ipv6_scope': ['ULA', 'GUA'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.16.0',
                'ipv4_prefix_length': 20,
                'tags': 'docker-local-egress',
                'egress': ['docker-local-ingress'],
                'ingress': [],
                'ipv6_network': '::ff10:fff0:ff16',
                'ipv6_scope': ['ULA'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.32.0',
                'ipv4_prefix_length': 20,
                'tags': ['docker-local-ingress'],
                'egress': [],
                'ingress': ['docker-local-egress'],
                'ipv6_network': '::ff10:fff0:ff32',
                'ipv6_scope': ['ULA'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.48.0',
                'ipv4_prefix_length': 20,
                'tags': ['docker-local-layer2'],
                'egress': [],
                'ingress': [],
                'ipv6_network': '::ff10:fff0:ff48',
                'ipv6_scope': ['LL'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.64.0',
                'ipv4_prefix_length': 20,
                'tags': ['docker-internet-egress'],
                'egress': ["internet"],
                'ingress': [],
                'ipv6_network': '::ff10:fff0:ff64',
                'ipv6_scope': ['GUA'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.80.0',
                'ipv4_prefix_length': 20,
                'tags': ['docker-internet-ingress'],
                'egress': [],
                'ingress': ["internet"],
                'ipv6_network': '::ff10:fff0:ff80',
                'ipv6_scope': ['GUA'],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.96.0',
                'ipv4_prefix_length': 20,
                'ipv6_network': '::ff10:fff0:ff96',
                'ipv6_scope': [],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.112.0',
                'ipv4_prefix_length': 20,
                'ipv6_network': '::ff10:fff0:f112',
                'ipv6_scope': [],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }, {
                'ipv4_network': '10.0.128.0',
                'ipv4_prefix_length': 20,
                'ipv6_network': '::ff10:fff0:f128',
                'ipv6_scope': [],
                'ipv6_prefix_length': 116,
                'subnet_template': 'default'
            }]
        }]}

    def get_schema_or_default(self):
        return self._default_schema

    def instantiate_scopes_from_schema(self):
        schema = self.get_schema_or_default()
        scopes_out = []
        parents = []
        to_process = schema.get("scopes")
        current = to_process.pop()

        while True:
            if current.get("ipv4_network") != None:
                cur4 = scope(parent = len(parents) > 0 and parents[-1][0] or None,
                             network_object = get_network_object(current.get("ipv4_network"), current.get("ipv4_prefix_length")))

            if current.get("ipv6_network") != None:
                cur6 = scope(parent = len(parents) > 0 and parents[-1][1] or None,
                             network_object = get_network_object(current.get("ipv6_network"), current.get("ipv6_prefix_length")))

            if current.get("subnet_template") != None:
                _ = [scopes_out.append(s) for s in self.template_to_scopes(schema, current.get("subnet_template"), cur4, cur6)]

            if current.get("scopes") != None:
                to_add = current.get("scopes")
                parent_t = (cur4 != None or cur6 != None) and (cur4, cur6) or None
                for index in to_add:
                    index["parent"] = hash(parent_t)
                    to_process.append(index)
                parents.append(parent_t)

            if len(to_process) != 0:
                current = to_process.pop()
            else:
                break

            if len(parents) > 0 and current.get("parent") != hash(parents[-1]):
                _ = parents.pop()

            cur4, cur6 = (None, None)

    def template_to_scopes(self, schema, template_name, current_v4 = None, current_v6 = None):
        template = next((template for template in schema.get("templates") if template.get("name") == template_name))
        for scope_template in template.get("scopes"):
            for s in get_network_object(
                current_v4.get("ipv4_network"),
                current_v4.get("ipv4_prefix_length")).subnets(
                    scope_template.get("ipv4_prefix_length")):
                yield scope(network_object = s, parent = current_v4)

    def __init__(self):
        pass

