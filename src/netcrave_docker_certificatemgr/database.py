import psycopg
import os

class docker_network_certificatemgr_database_client():
    def __init__(self):
        pass

    def get_container_certificates(self):
        pass

    def database(self):
        return psycopg.connect(os.environ.get("CERTIFICATEMGR_DB_CONNECT_STRING"))
