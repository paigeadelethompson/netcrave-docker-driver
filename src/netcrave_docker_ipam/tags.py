from netcrave_docker_ipam.db import ipam_database_client
from netcrave_docker_ipam.label import scope_label_masks, interface_type, tag_type


def instantiate_tags(tags, kind):
    if tags is not None:
        return [tag(kind, index) for index in tags]
    else:
        return []


class tag():
    def __init__(self,
                 tag_type,
                 name, id=None,
                 vrf_id=None,
                 route_table_id=None,
                 netns_name=None,
                 label_mask=None):

        self._name = name
        self._type = tag_type
        self._id = id
        self._vrf_id = vrf_id
        self._route_table_id = route_table_id
        self._netns_name = netns_name
        self._label_mask = label_mask

    def vrf_id(self):
        return self._vrf_id

    def netns_name(self):
        return self._netns_name

    def name(self):
        return self._name

    def id(self):
        return self._id

    def tag_type(self):
        return self._type

    def exists(self, cursor):
        query = """
        SELECT id, name, type, vrf_id, route_table_id, netns_name, label_mask
        FROM pools.tags
        WHERE name = %s AND type = %s
        LIMIT 1
        """
        (id,
         name,
         type,
         vrf_id,
         route_table_id,
         netns_name,
         label_mask) = cursor.cursor().execute(
             query, (self.name(), self.tag_type())).fetchone()
        return id is not None and True or False

    def save(self, cursor):
        if not self.exists(cursor):
            query = """
            INSERT INTO pools.tags(name, type)
            VALUES (%s, %s)
            RETURNING id
            """
            c = cursor.cursor()
            c.execute(query, (self.name(), self.tag_type()))
            self._id, _ = c.fetchone()


def load_tags_from_database(tags):
    with ipam_database_client().database() as conn:
        cursor = conn.cursor()
        with conn.transaction():
            err = [
                cursor.execute(
                    "SELECT * FROM pools.tags WHERE name = %s AND type = %s",
                    (tag_name, tag_type)) for tag_name, tag_type in tags]
            tags = [tag(t, name, id=id) for id, t, name in cursor.fetchall()]
            return tags
