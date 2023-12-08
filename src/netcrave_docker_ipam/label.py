from enum import Enum

class scope_label_masks(Enum):
    ZZZ_agate_scope_tags = 0x8
    ZZZ_agate_egress_tags = 0xf
    ZZZ_agate_ingress_tags = 0x20
    ZZZ_agate_route_table_id = 0x40
    ZZZ_agate_vrf_id = 0x80
    ZZZ_agate_network_ns = 0xff
    
    def default():
        return (scope_label_masks.ZZZ_agate_egress_tags.value
                | scope_label_masks.ZZZ_agate_ingress_tags.value
                | scope_label_masks.ZZZ_agate_network_ns.value
                | scope_label_masks.ZZZ_agate_route_table_id.value
                | scope_label_masks.ZZZ_agate_scope_tags.value
                | scope_label_masks.ZZZ_agate_vrf_id.value)
    
    def propagate_egress_tags(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_egress_tags.value) != 0 and True or False
    
    def propagate_ingress_tags(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_ingress_tags.value) != 0 and True or False
    
    def propagate_scope_tags(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_egress_tags.value) != 0 and True or False
    
    def propagate_route_table_id(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_route_table_id.value) != 0 and True or False
    
    def propagate_network_ns(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_network_ns.value) != 0 and True or False
    
    def propagate_vrf_id(_label_mask): 
        return (_label_mask & scope_label_masks.ZZZ_agate_vrf_id.value) != 0 and True or False
 
