import os
from flask import request, Response
from werkzeug.serving import run_simple

#from netcrave_docker_acme.acme import initiate_lets_encrypt_request
from netcrave_docker_davfs.dav_mem_backed_handler import memory_backed_descriptor
from netcrave_docker_util.http import http_servers
from netcrave_docker_util.flask import netcrave_flask

def acme_result(message):
    raise NotImplementedError()

#processor = processor(lambda message: acme_result(message), os.environ.get("ACME_PROCESSOR_LISTEN_ADDR"))

cert_mgr = netcrave_flask(__name__)
"""
"GET", 
    "HEAD", 
    "LOCK", 
    "MKCOL", 
    "MOVE", 
    "OPTIONS", 
    "POST", 
    "PROPFIND", 
    "PROPPATCH", 
    "PUT", 
    "TRACE", 
    "UNLOCK"])
def delete(request): 
    pass
"""

@cert_mgr.route('/', methods = ["COPY"])
def copy(request): 
    pass

@cert_mgr.route('/', methods = ["DELETE"])
def delete(request): 
    pass

@cert_mgr.route('/', methods = ["GET"])
def get(request): 
    pass

@cert_mgr.route('/', methods = ["HEAD"])
def head(request): 
    pass

@cert_mgr.route('/', methods = ["LOCK"])
def lock(request): 
    pass

@cert_mgr.route('/', methods = ["MKCOL"])
def _delete(request): 
    pass

@cert_mgr.route('/', methods = ["MOVE"])
def move(request): 
    pass

def run_job_processor():
        processor.run()

servers = http_servers(cert_mgr)

def run_cert_mgr():
    for index in servers:
        index.get("thread").start()
    for index in servers:
        index.get("thread").join()
