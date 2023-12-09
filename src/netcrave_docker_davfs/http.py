import os
from flask import Flask, request, Response
from werkzeug.serving import run_simple
from netcrave_docker_davfs.fs import fuse_dav_filesystem 
from flask_classful import FlaskView, route
import json

volume_driver = Flask(__name__)
volume_map = {}

def deserialize_request(request):
    return json.loads(request)

@volume_driver.route('/Plugin.Activate',           methods = ['POST'])
def activate(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Create',       methods = ['POST'])
def create(request):
    request_d = deserialize_request(request)
    volume_name = request.get("volume_name")
    options = request.get("Opts")
    dav_target = options.get("dav_target")
    
    volume_map[volume_name] = fuse_dav_filesystem(dav_target)
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Remove',       methods = ['POST'])
def remove(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Path',         methods = ['POST'])
def path(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Mount',        methods = ['POST'])
def mount(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Unmount',      methods = ['POST'])
def unmount(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.List',         methods = ['POST'])
def list_files(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Get',          methods = ['POST'])
def get_file(request):
    raise NotImplementedError()

@volume_driver.route('/VolumeDriver.Capabilities', methods = ['POST'])
def capabilities(request):
    raise NotImplementedError()

def run_volume_driver():
    if os.environ.get("DAVFS_SOCK") == None:
        path = "/run/docker/plugins"
        os.makedirs(path, exist_ok=True)
        path = "unix://{}/ipam".format(path)
    else:
        path = os.environ.get("DAVFS_SOCK")
        
    run_simple(
        hostname     = path,
        port         = 0,
        application  = volume_driver,
        use_reloader = True)
