
from netcrave_docker_ipam.db import ipam_database_client
from netcrave_docker_ipam.schema import uuid_to_address_object, get_network_object, network_object_to_uuid
from netcrave_docker_ipam.tags import tag
import uuid

class scope():
    _modified = False

    def __init__(self, id = None, prefix_length = None, parent = None, created = None, allocated = False, tags = [], network_object = None):
        self._id = uuid.UUID(id)
        self._prefix_length = prefix_length
        self._parent = parent
        self._created = created
        self._allocated = allocated
        self._tags = tags

        if id != None and network_object == None:
            self._network_object = get_network_object(uuid_to_address_object(uuid.UUID(id)), prefix_length)
        elif network_object != None:
            self._network_object = network_object
        else:
            raise NotImplementedError("scope must be instantiated with id/prefixlen or network object")

    def modified(self):
        return self._modified

    def created(self):
        return self._created

    def allocated(self):
        pass

    def id(self):
        return self._id

    def prefix_length(self):
        return self._prefix_length

    def network(self):
        pass

    def parent(self):
        pass

    def toggle_allocation_status(self):
        pass

    def exists(self):
        pass

    def ingress_tags(self):
        return [tag for tag in self._tags if tag.type == 'ingress']

    def egress_tags(self):
        return [tag for tag in self._tags if tag.type == 'egress']

    def scope_tags(self):
        return [tag for tag in self._tags if tag.type == 'scope']

    def save(self):
        pass


def get_scopes_by_tags(tags):
    with ipam_database_client().database() as conn:
        cursor = conn.cursor():
        with conn.transaction():
            err = [cursor.execute("""
            SELECT s.id, s.prefix_length, s.parent, s.created, s.modified, s.allocated from scope_tags f JOIN scopes s on f.scope = s.id
            WHERE f.tag = %s
            """, [index.id()]) for index in tags]
            return [scope(
                id = id,
                prefix_length = prefix_length,
                parent = parent,
                created = created,
                allocated = allocated,
                modified = modified) for id,
                    prefix_length,
                    parent,
                    created,
                    modified,
                    allocated in cursor.fetchall()]
