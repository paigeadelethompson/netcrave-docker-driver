# IAmPaigeAT (paige@paige.bio) 2023

from enum import Enum, auto


class tag_type(Enum):
    egress = auto()
    ingress = auto()
    scope = auto()


class scope_label_masks(Enum):
    p__scope_tags = 0x8
    p__egress_tags = 0xf
    p__ingress_tags = 0x20
    p__route_table_id = 0x40
    p__vrf_id = 0x80
    p__network_ns = 0xff

    @staticmethod
    def default():
        return (scope_label_masks.p__egress_tags.value
                | scope_label_masks.p__ingress_tags.value
                | scope_label_masks.p__network_ns.value
                | scope_label_masks.p__route_table_id.value
                | scope_label_masks.p__scope_tags.value
                | scope_label_masks.p__vrf_id.value)

    @staticmethod
    def propagate_egress_tags(_label_mask):
        return (
            _label_mask & scope_label_masks.p__egress_tags.value) != 0 and True or False

    @staticmethod
    def propagate_ingress_tags(_label_mask):
        return (
            _label_mask & scope_label_masks.p__ingress_tags.value) != 0 and True or False

    @staticmethod
    def propagate_scope_tags(_label_mask):
        return (
            _label_mask & scope_label_masks.p__egress_tags.value) != 0 and True or False

    @staticmethod
    def propagate_route_table_id(_label_mask):
        return (
            _label_mask & scope_label_masks.p__route_table_id.value) != 0 and True or False

    @staticmethod
    def propagate_network_ns(_label_mask):
        return (
            _label_mask & scope_label_masks.p__network_ns.value) != 0 and True or False

    @staticmethod
    def propagate_vrf_id(_label_mask):
        return (
            _label_mask & scope_label_masks.p__vrf_id.value) != 0 and True or False


class interface_type(Enum):
    (amt, bareudp, bond, bridge, can, dsa, dummy, erspan, geneve, gre, gretap, gtp,
     hsr, ifb, ip6erspan, ip6gre, ip6gretap, ip6tnl, ipip, ipoib, ipvlan, ipvtap,
     lowpan, macsec, macvlan, macvtap, netdevsim, nlmon, rmnet, sit, vcan, veth,
     virt_wifi, vlan, vrf, vti, vxcan, vxlan, xfrm) = (
         auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(),
         auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(),
         auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(),
         auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto(), auto())
