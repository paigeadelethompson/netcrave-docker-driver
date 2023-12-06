import sys, logging, json
from flask import Flask, request, Response
from netcrave_docker_ipam.service import service
from werkzeug.serving import run_simple
import os

flask_app = Flask(__name__)

s = service()

@flask_app.errorhandler(NotImplementedError)
def handle_invalid_usage(error):
    pass

@flask_app.route('/Plugin.Activate',                    methods = ['POST'] )
def Activate():
    pass

@flask_app.route('/IpamDriver.GetCapabilities',         methods = ['POST'] )
def GetCapabilities():
    pass

@flask_app.route('/IpamDriver.GetDefaultAddressSpaces', methods = ['POST'] )
def GetDefaultAddressSpaces():
    pass

@flask_app.route('/IpamDriver.RequestPool',             methods = ['POST'])
def RequestPool():
    pass

@flask_app.route('/IpamDriver.ReleasePool',             methods = ['POST'])
def ReleasePool():
    pass

@flask_app.route('/IpamDriver.RequestAddress',          methods = ['POST'])
def RequestAddress():
    pass

@flask_app.route('/IpamDriver.ReleaseAddress',          methods = ['POST'])
def ReleaseAddress():
    pass

def main():
    if os.environ.get("IPAMD_SOCK") == None:
        path = "/run/docker/plugins"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/ipam".format(path)
    else:
        path = os.environ.get("IPAM_SOCK")
        
    run_simple(
        hostname     = path,
        port         = 0,
        application  = flask_app,
        use_reloader = True)
