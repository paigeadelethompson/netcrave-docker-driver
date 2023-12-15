import requests
import tarfile
from pathlib import Path
from itertools import islice
import platform
from tempfile import mktemp
import sys 

class installer():
    def _tarfile_mapper(
        self, 
        archive, 
        path_formatter = lambda path: "/opt/netcrave/{path}".format(path = path), 
        exclude_file = lambda path: False):
        return [{ "src": index, "dst": path_formatter(index) } for index in tarfile.open(archive).getnames() if not exclude_file(index)]
    
    def __init__(self):
        self._packages = [{
                "x86_64": "https://github.com/kata-containers/kata-containers/releases/download/3.2.0/kata-static-3.2.0-amd64.tar.xz",
                "map": lambda archive: self._tarfile_mapper(archive, lambda path: (path.replace(
                    "/opt/kata", 
                    "/opt/netcrave")))
            },
            {
                "x86_64": "https://github.com/opencontainers/runc/releases/download/v1.1.10/runc.amd64",
                "dst": "/opt/netcrave/sbin/runc"
                
            },
            {
                "x86_64": "https://github.com/containerd/containerd/releases/download/v1.7.11/containerd-1.7.11-linux-amd64.tar.gz",
                "map": lambda archive: self._tarfile_mapper(archive)
            },
            {
                "x86_64": "https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz",
                "map": lambda archive: self._tarfile_mapper(archive, lambda path: (
                    "/opt/netcrave/bin/{path}".format(path = "/".join(path.split("/")[1::]))))
                    
            },
            {
                "x86_64": "https://download.docker.com/linux/static/stable/x86_64/docker-rootless-extras-24.0.7.tgz",
                "map": lambda archive: self._tarfile_mapper(archive, lambda path: (path.replace(
                    "docker-rootless-extras", 
                    "/opt/netcrave/bin")))
            },
            {
                "x86_64": "https://storage.googleapis.com/gvisor/releases/release/latest/amd64/containerd-shim-runsc-v1",
                "dst": "/opt/netcrave/sbin/containerd-shim-runsc-v1"
                
            },
            {
                "x86_64": "https://storage.googleapis.com/gvisor/releases/release/latest/amd64/runsc",
                "dst": "/opt/netcrave/sbin/runsc"
            },
            {
                "x86_64": "https://github.com/firecracker-microvm/firecracker/releases/download/v1.5.1/firecracker-v1.5.1-x86_64.tgz",
                "map": (lambda archive: self._tarfile_mapper(
                    archive, 
                    lambda path: (path.replace(
                        "release-v1.5.1-x86_64", 
                        "/opt/netcrave/bin")),
                    lambda path: (len([index for index in (
                        "CHANGES", 
                        "THIRD-PARTY", 
                        "SHA256SUMS",
                        "NOTICE",
                        "LICENSE",
                        ".debug",
                        ".yaml",
                        ".json") if path.endswith(index)])) > 0))
            }]
        
    def install_all(self):
        for index in self._packages:
            if index.get("dst") != None and not Path(index.get("dst")).parent.exists():
                Path.mkdir(Path(index.get("dst")).parent, parents = True, exist_ok = True)
                print("created directory {direc}".format(direc = Path(index.get("dst")).parent))
            
            dl = index.get("dst") != None and index.get("dst") or mktemp()

            print("retrieving {url}".format(url = index.get(platform.machine())))
            with open(dl, 'wb') as f:
                r = requests.get(index.get(platform.machine()), allow_redirects = True)
                f.write(r.content)
                print("wrote {filename}".format(filename = dl))
            if index.get("map") != None:
                file_map = index.get("map")(dl)
                tar = tarfile.open(dl)
                for member in tar.getmembers():
                    for mapped in file_map:
                        if mapped.get("src") == member.name:                            
                            tar.extract(member, mapped.get("dst"))
                            print("extracted file {filename}".format(filename = mapped.get("dst")))
                            
            if index.get("dst") == None:
                print("deleting {tempfile}".format(tempfile = dl)
                Path(dl).unlink()
                            
