import os
from flask import Flask, request, Response
from werkzeug.serving import run_simple

from netcrave_docker_zmq.processor import processor
from netcrave_docker_acme.acme import initiate_lets_encrypt_request

jobs = {}

def queue_new_job(message):
    raise NotImplementedError()

processor = processor(lambda message: queue_new_job(message), os.environ.get("ACME_PROCESSOR_LISTEN_ADDR"))

acme = Flask(__name__)

@acme.route('/.well-known/acme-challenge/', methods = ['POST'])
def well_known_acme_challenge():
    raise NotImplementedError()
    
# https://github.com/certbot/certbot/blob/917e3aba6bb8b0c6aa7f0eaf5c9a8128b4e59531/acme/acme/challenges.py#L185
# looks like it might be the thumb print of the account key        

def run_job_processor():
        processor.run()

def run_acme():
    run_simple(
        hostname     = os.environ.get("ACME_LISTEN_ADDR"),
        application  = acme, 
        use_reloader = True)

