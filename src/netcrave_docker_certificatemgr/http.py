import os
from flask import Flask, request, Response
from werkzeug.serving import run_simple

from netcrave_docker_acme.acme import initiate_lets_encrypt_request
from netcrave_docker_davfs.dav_mem_backed_handler import memory_backed_descriptor

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
def run_job_processor():
        processor.run()

def run_cert_mgr():
    run_simple(
        hostname     = os.environ.get("CERT_MGR_LISTEN_ADDR"),
        application  = cert_mgr, 
        use_reloader = True)
