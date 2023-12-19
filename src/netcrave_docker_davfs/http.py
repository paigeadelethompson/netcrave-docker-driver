import os
from flask import request, Response
from netcrave_docker_util.flask import netcrave_flask
from werkzeug.serving import run_simple
import json

volume_driver = netcrave_flask(__name__)

"""
This part will use the client+fuse to target a DAV server (like certificatemgr)
"""

@volume_driver.route('/Plugin.Activate', methods = ['POST'])
def activate(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Create', methods = ['POST'])
def create(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Remove', methods = ['POST'])
def remove(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Path', methods = ['POST'])
def path(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Mount', methods = ['POST'])
def mount(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Unmount', methods = ['POST'])
def unmount(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.List', methods = ['POST'])
def list_files(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Get', methods = ['POST'])
def get_file(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Capabilities', methods = ['POST'])
def capabilities(request):
    raise NotImplementedError()

def run_volume_driver():
    if os.environ.get("DAVFS_SOCK") == None:
        path = "/run/docker/plugins/davfs"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/ipam".format(path)
    else:
        path = os.environ.get("DAVFS_SOCK")
        
    run_simple(
        hostname     = path,
        port         = 0,
        application  = volume_driver,
        use_reloader = True)
