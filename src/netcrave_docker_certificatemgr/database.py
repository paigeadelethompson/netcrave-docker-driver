# IAmPaigeAT (paige@paige.bio) 2023

import os
import psycopg


class docker_network_certificatemgr_database_client():
    def __init__(self):
        pass

    def get_persistent_certificates(self):
        raise NotImplementedError()

    def database(self):
        return psycopg.connect(os.environ.get("DB_CONNECT_STRING"))
