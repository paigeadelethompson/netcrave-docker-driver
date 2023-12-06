from netcrave_docker_ipam.db import ipam_database_client

class tag():
    def __init__(self, tag_type, name, id = None):
        self.name = Name
        self.type = type
        self.id = id

    def tag_name(self):
        pass

    def tag_id(self):
        pass

    def tag_type(self):
        pass

    def save(self):
        pass

def get_tags(tags):
    with ipam_database_client().database() as conn:
        cursor = conn.cursor():
        with conn.transaction():
            err = [cursor.execute("SELECT * FROM pools.tags WHERE name = %s AND type = %s", [tag_name, tag_type]) for tag_name, tag_type in tags]
            tags = [tag(tag_type = t, name = name, id = id) for id, t, name in cursor.fetchall()]
            return tags
