# IAmPaigeAT (paige@paige.bio) 2023

import os, time
from flask import Flask, request, Response
from netcrave_docker_util.http import http_server
from netcrave_docker_zmq.processor import processor
from netcrave_docker_acme.acme import initiate_lets_encrypt_request

jobs = {}

def queue_new_job(message):
    raise NotImplementedError()

processor = processor(lambda message: queue_new_job(message), os.environ.get("ACME_PROCESSOR_LISTEN_ADDR"))

acme = Flask(__name__)

servers = http_servers(acme)

@acme.route('/.well-known/acme-challenge/', methods = ['POST'])
def well_known_acme_challenge():
    raise NotImplementedError()
    
# https://github.com/certbot/certbot/blob/917e3aba6bb8b0c6aa7f0eaf5c9a8128b4e59531/acme/acme/challenges.py#L185
# looks like it might be the thumb print of the account key        

def run_job_processor():
        processor.run()

def run_acme():
    for index in servers:
        servers.get("thread").start()
    for index in servers:
        servers.get("thread").join()
