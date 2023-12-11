import os
from flask import Flask, request, Response
from werkzeug.serving import run_simple

from netcrave_docker_acme.acme import initiate_lets_encrypt_request
from netcrave_docker_davfs.dav_mem_backed_handler import memory_backed_descriptor
from netcrave_docker_util.http import http_servers

def acme_result(message):
    raise NotImplementedError()

processor = processor(lambda message: acme_result(message), os.environ.get("ACME_PROCESSOR_LISTEN_ADDR"))

cert_mgr = Flask(__name__)

@cert_mgr.route('/', methods = [
    "COPY", 
    "DELETE", 
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
def dav_request(request): 
    pass 

def run_job_processor():
        processor.run()

servers = http_servers(cert_mgr, bind_addresses = [("unix://run/netcrave/sock", 0, False, 0.5)])

def run_cert_mgr():
    for index in servers:
        index.start()
    for index in servers:
        index.join()
