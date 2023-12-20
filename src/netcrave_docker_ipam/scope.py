# IAmPaigeAT (paige@paige.bio) 2023

import uuid
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, ip_address
from netcrave_docker_ipam.db import ipam_database_client
from netcrave_docker_ipam.label import scope_label_masks, interface_type


def get_network_object(network, prefix_length):
    net = ip_address(network)
    if isinstance(net, IPv4Address):
        return IPv4Network(net).supernet(new_prefix=prefix_length)
    elif isinstance(net, IPv6Address):
        return IPv6Network(net).supernet(new_prefix=prefix_length)


def network_object_to_uuid(network):
    if isinstance(network, IPv4Network):
        return uuid.UUID(
            bytes=bytes(
                [0x00] *
                12) +
            network.network_address.packed)
    elif isinstance(network, IPv6Network):
        return uuid.UUID(bytes=network.network_address.packed)


def uuid_to_address_object(id):
    if int.from_bytes(id.bytes[:12]) == 0:
        return IPv4Address(int.from_bytes(id.bytes[12:16]))
    else:
        return IPv6Address(int.from_bytes(id.bytes))


def get_ipv6_network_object_from_token(parent, token, prefix_len):
    net_bytes = [
        index for index in parent.network_address.packed[::-1] if index != 0][::-1]
    token_bytes = [index for index in IPv6Address(token).packed if index != 0]
    zeroes = 16 - len(net_bytes + token_bytes)
    return IPv6Network(IPv6Address(
        int.from_bytes(
            bytes(net_bytes)
            + bytes(token_bytes)
            + bytes([0] * zeroes)))).supernet(
                new_prefix=prefix_len)


class scope():
    _modified = False

    def __str__(self):
        return str(self.network_object())

    def __init__(self,
                 network_object,
                 parent=None,
                 created=None,
                 modified=None,
                 allocated=False,
                 tags=[],
                 allocation_length=32,
                 route_table_id=2,
                 vrf_id=2,
                 label_mask=None):

        self._network_object = network_object
        self._parent = parent
        self._created = created
        self._allocated = allocated
        self._tags = tags
        self._allocation_length = allocation_length
        self._route_table_id = route_table_id
        self._vrf_id = vrf_id
        self._label_mask = label_mask

    def allocation_length(self):
        return self._allocation_length

    def route_table_id(self):
        return self._route_table_id

    def set_label(self, label_mask=scope_label_masks.default()):
        self._label_mask = label_mask

    def network_interface_name(self):
        raise NotImplementedError()

    def network_namespace(self):
        raise NotImplementedError()

    def network_interface_kind(self):
        if self.prefix_length() == 31 or self.prefix_length() == 127:
            return interface_type.veth
        elif self.network_object().network_address == IPv4Address(
            "169.254.169.254") or self.network_object(
        ).network_address == IPv6Address("fe80:ffff:ffff:ffff:ffff:ffff:ffff:ffff"):
            return interface_type.dummy
        elif self.prefix_length() == 32 or self.prefix_length() == 128:
            return interface_type.veth
        else:
            return interface_type.bridge

    def acquire_unallocated_address(self):
        raise NotImplementedError()

    def network_gateway_address(self):
        raise NotImplementedError()

    def network_vrf_id(self):
        return self._vrf_id

    def id(self):
        return network_object_to_uuid(self._network_object)

    def network_object(self):
        return self._network_object

    def modified(self):
        return self._modified

    def created(self):
        return self._created

    def allocated(self):
        return self._allocated

    def prefix_length(self):
        return self._network_object.prefixlen

    def network_address(self):
        return self._network_object.network_address

    def parent(self):
        return self._parent

    def toggle_allocation_status(self):
        self._allocated = not self._allocated

    def exists(self, cursor):
        query = """
        SELECT * FROM pools.scopes
        WHERE id = %s
        LIMIT 1
        """
        return cursor.execute(
            query, (self.id(), )).fetchone() is not None and True or False

    def ingress_tags(self, cursor):
        return [tag for tag in self._tags if tag.tag_type() ==
                cursor.tag_type().enum.scope]

    def egress_tags(self, cursor):
        return [tag for tag in self._tags if tag.tag_type() ==
                cursor.tag_type().enum.egress]

    def scope_tags(self, cursor):
        return [tag for tag in self._tags if tag.tag_type() ==
                cursor.tag_type().enum.ingress]

    def _save_scope_tag_fk(self, cursor):
        query = """
        INSERT INTO pools.scope_tags(scope, tag)
        VALUES ( %s, %s )
        """
        for index in self._tags:
            cursor.execute(query, (self.id(), index.id()))

    def save(self, cursor):
        if self.parent() is not None:
            self.parent().save(cursor)

        for index in self._tags:
            index.save(cursor)

        if not self.exists(cursor):
            query = """
            INSERT INTO pools.scopes
            VALUES (%s, %s, %s, NOW(), NOW(), %b)
            RETURNING created, modified
            """
            c = cursor.cursor()
            c.execute(
                query,
                (self.id(),
                 self.parent() is not None and self.parent().id() or uuid.UUID(
                    bytes=bytes(
                        [0] * 16)),
                    self.prefix_length().to_bytes(),
                    self.allocated()))

            self._created, self._modified = c.fetchone()
            self._save_scope_tag_fk(cursor)


def get_scopes_by_tags(tags):
    conn = ipam_database_client().database()
    cursor = conn.cursor()
    with conn.txn():
        err = [cursor.execute("""
        SELECT s.id, s.prefix_length, s.parent, s.created, s.modified, s.allocated from scope_tags f
        JOIN scopes s on f.scope = s.id
        WHERE f.tag = %s
        """, [index.id()]) for index in tags]
    raise NotImplementedError()
