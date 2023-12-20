# IAmPaigeAT (paige@paige.bio) 2023

import psycopg
import os

from psycopg.types.enum import EnumInfo, register_enum
from psycopg.errors import InvalidCatalogName
from netcrave_docker_ipam.label import tag_type


class ipam_database_cursor():
    def __init__(self, db, tag_type_info):
        self._tag_type_info = tag_type_info
        self._db = db

    def cursor(self):
        return self._db.cursor()

    def tag_type(self):
        return self._tag_type_info

    def execute(self, *args):
        return self._db.cursor().execute(*args)

    def txn(self):
        return self._db.transaction()

    def _(self):
        return self._db


class ipam_database_client():
    _create_db_query = """
    CREATE DATABASE IF NOT EXISTS netcrave;
    """

    _create_schema_query = """
    CREATE SCHEMA IF NOT EXISTS pools
    AUTHORIZATION root;
    """

    _create_scope_table_query = """
    CREATE TABLE IF NOT EXISTS pools.scopes
    (
    id uuid NOT NULL,
    parent uuid,
    prefix_length bytea NOT NULL DEFAULT '\x20'::bytea,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    allocated bool DEFAULT false,
    allocation_length bytea NOT NULL DEFAULT '\x20'::bytea,
    vrf_id int DEFAULT 2,
    route_table_id int DEFAULT 2,
    netns_name name,
    label_mask bytea,
    CONSTRAINT pools_index PRIMARY KEY (id),
    CONSTRAINT pools_identity UNIQUE (id, prefix_length)
    );
    ALTER TABLE IF EXISTS pools.scopes
    OWNER to root;
    """

    _create_tag_type_query = """
    CREATE TYPE IF NOT EXISTS pools.tag AS ENUM
    ('ingress', 'egress', 'scope');
    ALTER TYPE pools.tag
    OWNER TO root;
    """

    _create_tag_table_query = """
    CREATE TABLE IF NOT EXISTS pools.tags
    (
    id serial NOT NULL,
    type pools.tag NOT NULL,
    name name NOT NULL,
    vrf_id int DEFAULT 2,
    route_table_id int DEFAULT 2,
    netns_name name,
    label_mask bytea,
    CONSTRAINT tags_index PRIMARY KEY (id),
    CONSTRAINT tags_identity UNIQUE (type, name)
    );
    ALTER TABLE IF EXISTS pools.tags
    OWNER to root;
    """

    _create_scope_tag_table_query = """
    CREATE TABLE IF NOT EXISTS pools.scope_tags
    (
    id serial NOT NULL,
    scope uuid NOT NULL,
    tag bigint NOT NULL,
    CONSTRAINT scope_tags_index PRIMARY KEY (id),
    CONSTRAINT scope_tag_identity UNIQUE (scope, tag),
    CONSTRAINT fk_scope FOREIGN KEY (scope)
        REFERENCES pools.scopes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT fk_tags FOREIGN KEY (tag)
        REFERENCES pools.tags (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
    );
    ALTER TABLE IF EXISTS pools.scope_tags
    OWNER to root;
    """

    def tag_type_info(self):
        return self._tag_type_info

    def setup(self, conn_string=os.environ.get("DB_CONNECT_STRING"), ex=None):
        try:
            if ex is not None:
                self._conn = psycopg.connect(
                    conn_string.replace(
                        "netcrave",
                        "defaultdb"),
                    autocommit=True)
                self.create_database(ex)
                self._conn.close()
                self._conn = psycopg.connect(conn_string, autocommit=True)
                self.create_database()
                self._tag_type_info = EnumInfo.fetch(self._conn, "pools.tag")
                register_enum(self._tag_type_info, self._conn, tag_type)
            else:
                self._conn = psycopg.connect(conn_string, autocommit=True)
                self._tag_type_info = EnumInfo.fetch(self._conn, "pools.tag")
                register_enum(self._tag_type_info, self._conn, tag_type)
        except InvalidCatalogName as e:
            if ex is None:
                self.setup(ex=e)
            else:
                raise Exception(
                    "first error: {} second error: {} couldn't create database".format(
                        ex, e))

    def __init__(self):
        if os.environ.get("DB_CONNECT_STRING") is None:
            raise NotImplementedError("env connection string required")
        else:
            self.setup()

    def database(self):
        return ipam_database_cursor(self._conn, self._tag_type_info)

    def delete_database(self):
        self._conn.execute("DROP DATABASE netcrave")

    def create_database(self, ex=None):
        if ex is not None:
            self._conn.execute(self._create_db_query)
            return

        self._conn.execute(self._create_schema_query)
        self._conn.execute(self._create_tag_type_query)
        self._conn.execute(self._create_tag_table_query)
        self._conn.execute(self._create_scope_table_query)
        self._conn.execute(self._create_scope_tag_table_query)
