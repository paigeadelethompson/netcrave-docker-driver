# IAmPaigeAT (paige@paige.bio) 2023

import uuid
from netcrave_docker_ipam.scope import scope, get_network_object, get_ipv6_network_object_from_token
from netcrave_docker_ipam.tags import tag, instantiate_tags
from netcrave_docker_ipam.label import scope_label_masks, interface_type, tag_type
from itertools import islice
from  sys import maxsize as MAX
import os 

class schema():
    def __init__(self):
        self._default_schema = {
            'reserved_vrf_ids': [1],
            'schema_version': 2,
            'templates': [{
                'name': 'default',
                'scopes': [{
                    'ipv4_prefix_length': 21,
                    'ipv6_prefix_length': 117
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
    
    def default_vrf_id(self): 
        return os.environ.get("DEFAULT_VRF_ID")
    
    def default_route_table(self):
        return os.environ.get("DEFAULT_ROUTE_TABLE")
    
    def default_network_namespace(self):
        return os.environ.get("DEFAULT_NETWORK_NS")
    
    def get_schema_or_default(self):
        return self._default_schema

    def instantiate_scopes_from_schema(self, cursor):
        schema = self.get_schema_or_default()
        to_process = schema.get("scopes")
        current_parent, current, current_deserialized = (None, None, None)
        
        while True:
            if len(to_process) <= 0:
                break
            
            current_parent = current_deserialized
            current_deserialized = None
            current = to_process.pop()
            
            if current.get("parent") != None and hash(
                current.get("parent")) != hash(current_parent):
                current_parent = None
                
            if current.get("ipv4_network"):
                current_deserialized = self.parse_current_scopev4(current)
                
                yield current_deserialized
                
                if current.get("subnet_template") != None and current_deserialized != None:
                    for index in self.template_to_scopes(
                        schema, 
                        current.get("subnet_template"), 
                        current_deserialized):
                        yield index
                    
                to_process = to_process + self.parse_nested_scopes_v4(current_deserialized, current)
                
            if current.get("ipv6_network"):
                current_deserialized = self.parse_current_scopev6(current)
                
                yield current_deserialized
                
                if current.get("subnet_template") != None and current_deserialized != None:
                    for index in self.template_to_scopes(
                        schema, 
                        current.get("subnet_template"), 
                        current_deserialized, 
                        which = "ipv6_prefix_length"):
                        yield index
                        
                to_process = to_process + self.parse_nested_scopes_v6(current_deserialized, current)
                
    def parse_current_scopev4(self, current): 
        current_deserialized = scope(get_network_object(
                    current.get("ipv4_network"), 
                    current.get("ipv4_prefix_length")),
                tags = instantiate_tags(
                    current.get("tags"), tag_type.scope)
                    + instantiate_tags(
                    current.get("tags"), tag_type.egress)
                    + instantiate_tags(
                    current.get("tags"), tag_type.ingress),
                vrf_id = (current.get("vrf_id") != None 
                            and current.get("vrf_id") 
                            or self.default_vrf_id()),
                parent = (current.get("parent") != None 
                            and current.get("parent") 
                            or None))
                
        return current_deserialized
              
    def parse_current_scopev6(self, current):
        current_deserialized = scope(get_network_object(
                    current.get("ipv6_network"), 
                    current.get("ipv6_prefix_length")),
                tags = instantiate_tags(
                    current.get("tags"), tag_type.scope)
                    + instantiate_tags(
                    current.get("tags"), tag_type.egress)
                    + instantiate_tags(
                    current.get("tags"), tag_type.ingress),
                vrf_id = (current.get("vrf_id") != None 
                            and current.get("vrf_id") 
                            or self.default_vrf_id()),
                parent = (current.get("parent") != None 
                            and current.get("parent") 
                            or None))
                
        return current_deserialized
    
    def parse_nested_scopes_v6(self, current_deserialized, current):
        if current.get("scopes") != None and len(current.get("scopes")) > 0:
            nested_scopes = current.get("scopes")
            for index in nested_scopes:
                if index.get("ipv6_network") != None:
                    index["parent"] = current_deserialized
            return nested_scopes
        return []
                    
    def parse_nested_scopes_v4(self, current_deserialized, current): 
        if current.get("scopes") != None and len(current.get("scopes")) > 0:
            nested_scopes = current.get("scopes")
            for index in nested_scopes:
                    if index.get("ipv4_network") != None:
                        index["parent"] = current_deserialized
            return nested_scopes
        return []

    def template_to_scopes(self, schema, template_name, parent, which = "ipv4_prefix_length"):
        template = next((template for template in schema.get("templates") if template.get("name") == template_name))        
        last, current, networks = None, None, None
        
        for scope_template in sorted(
            [index for index in template.get("scopes") if index.get(which) != None],
            key = lambda k: k.get(which)):
                if last != None and last.prefixlen != scope_template.get(which):
                    networks = last.subnets(new_prefix = scope_template.get(which))        
                elif last == None:
                    networks = parent.network_object().subnets(new_prefix = scope_template.get(which))

                for current in networks:
                    last = current
                    yield scope(current,
                        tags = instantiate_tags(
                            scope_template.get("tags"), tag_type.scope)
                            + instantiate_tags(
                            scope_template.get("tags"), tag_type.egress)
                            + instantiate_tags(
                            scope_template.get("tags"), tag_type.ingress),
                        vrf_id = (scope_template.get("vrf_id") != None 
                                    and scope_template.get(vrf_id)
                                    or self.default_vrf_id()),
                        parent = parent)
