import psycopg
import os
from netcrave_docker_ipam.schema import schema

class ipam_database_client():
    _create_db_query = """
    CREATE DATABASE IF NOT EXISTS ipam;
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

    def __init__(self):
        pass

    def database(self):
        return psycopg.connect(os.environ.get("DB_CONNECT_STRING"))

    def _instantiate_schema(self):
        scopes = schema().instantiate_scopes_from_schema()


    def create_database(self):
        with self.database() as conn:
            cursor = conn.cursor()
            with conn.transaction():
                cursor.execute(self._create_db_query)
                cursor.execute(self._create_schema_query)
                cursor.execute(self._create_tag_type_query)
                cursor.execute(self._create_tag_table_query)
                cursor.execute(self._create_scope_table_query)
                cursor.execute(self._create_scope_tag_table_query)

                self._instantiate_schema()
