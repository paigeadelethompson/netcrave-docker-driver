from contextlib import contextmanager
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import josepy as jose
import OpenSSL

from acme import challenges
from acme import client
from acme import crypto_util
from acme import errors
from acme import messages
from acme import standalone
import os
from flask import Flask, request, Response
from werkzeug.serving import run_simple

import docker
import queue



message_queue_in = queue.Queue()
message_queue_out = queue.Queue()
queued_challenges = {}

volume_driver = Flask("volume_driver_{}".format(__name__))
dav           = Flask("dav_{}".format(__name__))
acme          = Flask("acme_{}".format(__name__))

@acme.route('/.well-known/acme-challenge/',        methods = ['POST'])
def well_known_acme_challenge():
    token = request.path.split('/')[-1]
    if queued_challenges.get(token) != None:
        pass

@volume_driver.errorhandler(NotImplementedError)
def handle_invalid_usage(error):
    pass

@volume_driver.route('/Plugin.Activate',           methods = ['POST'])
def activate():
    pass

@volume_driver.route('/VolumeDriver.Create',       methods = ['POST'])
def create():
    pass

@volume_driver.route('/VolumeDriver.Remove',       methods = ['POST'])
def remove():
    pass

@volume_driver.route('/VolumeDriver.Path',         methods = ['POST'])
def path():
    pass

@volume_driver.route('/VolumeDriver.Mount',        methods = ['POST'])
def mount():
    pass

@volume_driver.route('/VolumeDriver.Unmount',      methods = ['POST'])
def unmount():
    pass

@volume_driver.route('/VolumeDriver.List',         methods = ['POST'])
def _list():
    pass

@volume_driver.route('/VolumeDriver.Get',          methods = ['POST'])
def _get():
    pass

@volume_driver.route('/VolumeDriver.Capabilities', methods = ['POST'])
def capabilities():
    pass

@dav.route('/',          methods = ["COPY", 
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
def mem_dav_fs():
    pass

def await_acme_challenge_response():
    while True:
        msg = message_queue_in.get(block = True)
        if msg == None:
            break
        response, validation = msg.get(
            "challenge").response_and_validation(msg.get(
                "client").net.key)

        msg['response'] = response
        msg['validation'] = validation
        msg['handled'] = False
        # https://github.com/certbot/certbot/blob/917e3aba6bb8b0c6aa7f0eaf5c9a8128b4e59531/acme/acme/challenges.py#L185
        # looks like it might be the thumb print of the account key
        queued_challenges[msg.get("challenge").encode('token')] = msg


def run_volume_driver():
    if os.environ.get("VOLUME_SOCK") == None:
        path = "/run/docker/plugins"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/crtmgr".format(path)
    else:
        path = os.environ.get("VOLUME_SOCK")

    run_simple(hostname = path, port = 0, application = volume_driver, use_reloader = True)

def run_dav():
    if os.environ.get("DAV_SOCK") == None:
        path = "/run/netcrave/certificatemgr"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/dav".format(path)
    else:
        path = os.environ.get("DAV_SOCK")

    run_simple(hostname = path, port = 0, application = dav, use_reloader = True)

def run_acme():
    run_simple(hostname = 'http://[2001:db8:aaaa:aaad:192:0:0:14]:80',
               application = acme, use_reloader = True)

