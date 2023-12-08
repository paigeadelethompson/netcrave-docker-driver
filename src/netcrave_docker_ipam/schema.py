# IAmPaigeAT (paige@paige.bio) 2023

import uuid
from netcrave_docker_ipam.scope import scope, get_network_object, get_ipv6_network_object_from_token
from netcrave_docker_ipam.tags import tag
from netcrave_docker_ipam.db import tag_type
from itertools import islice
from  sys import maxsize as MAX

class schema():
    def __init__(self):
        self._default_schema = {
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
                'ipv6_network': 'fc00:ffff:ffff:ffff::',
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

    def instantiate_tags(self, tags, kind):
        if tags != None:
            return [tag(kind, index) for index in tags]
        else: 
            return []
        

    def instantiate_scopes_from_schema(self, cursor):
        schema = self.get_schema_or_default()
        scopes_out = []
        parents = []
        to_process = schema.get("scopes")
        current = to_process.pop()

        while True:
            if current.get("ipv4_network") != None:
                cur4 = scope(get_network_object(current.get("ipv4_network"), current.get("ipv4_prefix_length")),
                             parent = len(parents) > 0 and parents[-1][0] or None,
                             tags = self.instantiate_tags(current.get("tags"), cursor.tag_type().enum.scope)
                             + self.instantiate_tags(current.get("egress"), cursor.tag_type().enum.egress)
                             + self.instantiate_tags(current.get("tags"), cursor.tag_type().enum.ingress))

            if current.get("ipv6_network") != None:
                if current.get("ipv6_network").startswith("::"):
                    net6 = get_ipv6_network_object_from_token(
                        parents[-1][1].network_object(), 
                        current.get("ipv6_network"), 
                        current.get("ipv6_prefix_length"))
                else: 
                    net6 = get_network_object(current.get("ipv6_network"), current.get("ipv6_prefix_length"))
                    
                cur6 = scope(net6,
                             parent = len(parents) > 0 and parents[-1][1] or None,
                             tags = self.instantiate_tags(current.get("tags"), cursor.tag_type().enum.scope) 
                             + self.instantiate_tags(current.get("egress"), cursor.tag_type().enum.egress)
                             + self.instantiate_tags(current.get("ingress"), cursor.tag_type().enum.ingress))

            if current.get("subnet_template") != None:
                [scopes_out.append(s) for s in self.template_to_scopes(schema, current.get("subnet_template"), cur4, cur6)]

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
                parents.pop()

            scopes_out += [cur4, cur6]
            cur4, cur6 = (None, None)
            
        return scopes_out

    def template_to_scopes(self, schema, template_name, current_v4 = None, current_v6 = None):
        template = next((template for template in schema.get("templates") if template.get("name") == template_name))
        
        for scope_template in template.get("scopes"):
            if current_v4 != None:
                for s in current_v4.network_object().subnets(new_prefix = scope_template.get("ipv4_prefix_length")):
                    yield scope(s, parent = current_v4, allocation_length = scope_template.get("ipv4_allocation_length"))
            if current_v6 != None:
                for s in current_v6.network_object().subnets(new_prefix = scope_template.get("ipv6_prefix_length")):
                    yield scope(s, parent = current_v6, allocation_length = scope_template.get("ipv6_allocation_length"))
