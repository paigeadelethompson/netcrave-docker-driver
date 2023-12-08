from netcrave_docker_ipam.db import ipam_database_client, tag_type

class tag():
    def __init__(self, tag_type, name, id = None):
        self._name = name
        self._type = tag_type
        self._id = id

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
        return id != None and True or False

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
            err = [cursor.execute("SELECT * FROM pools.tags WHERE name = %s AND type = %s", 
                                  (tag_name, tag_type)) for tag_name, tag_type in tags]
            tags = [tag(t, name, id = id) for id, t, name in cursor.fetchall()]
            return tags
