# IAmPaigeAT (paige@paige.bio) 2023

import requests
import tarfile
from pathlib import Path
from itertools import islice
import platform
from tempfile import mktemp
import logging
import sys 
import asyncio
import aiofiles
import aiohttp 

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
                    "./opt/kata", 
                    "/opt/netcrave")),
                lambda path: (len([index for index in (
                        "versions.yaml",
                        "VERSION") if path.endswith(index)])) > 0)
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
                "name": "Firecracker",
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
            },
            {
                "name": "CRI-O",
                "desc": "https://cri-o.github.io/cri-o/",
                "x86_64": "https://storage.googleapis.com/k8s-conform-cri-o/artifacts/cri-o.amd64.52126218773e74abb6d3b92f431300a217da5ed8.tar.gz",
                "arm64": "https://storage.googleapis.com/k8s-conform-cri-o/artifacts/cri-o.arm64.52126218773e74abb6d3b92f431300a217da5ed8.tar.gz",
                "map": lambda archive: self._tarfile_mapper(archive, lambda path: (
                    "/opt/netcrave/{path}".format(path = "/".join(path.split("/")[1::]))),
                    lambda path: (len([index for index in (
                        "etc",
                        "crictl.yaml",
                        "crio.conf",
                        "crio-umount.conf",
                        "README.md",
                        "contrib",
                        "crio.service",
                        "crio.service",
                        "policy.json",
                        "10-crio-bridge.conf",
                        "Makefile") if path.endswith(index)])) > 0)
                    
            }]

    async def extract_archive(self, index, dl):
        log = logging.getLogger(__name__)
        if index.get("map") != None:
            file_map = index.get("map")(dl)
            tar = tarfile.open(dl)
            for member in tar.getnames():
                for mapped in file_map:
                    if mapped.get("src") == member:                            
                        file = tar.getmember(member)
                        if not file.isdir():
                            async with aiofiles.open(mapped.get("dst"), "wb") as out:
                                await out.write(tar.extractfile(member).read())
                                log.debug("extracted file {filename}".format(filename = mapped.get("dst")))
                            async with aiofiles.open(mapped.get("dst"), "rb") as check:                                                                
                                header = await check.read(2)
                                if (mapped.get("dst").startswith("/opt/netcrave/cni-plugins") 
                                    or mapped.get("dst").startswith("/opt/netcrave/bin") 
                                    or mapped.get("dst").startswith("/opt/netcrave/libexec")) and (
                                        header == bytes([0x7f, 0x45]) 
                                        or header == bytes([0x23, 0x21])):
                                    log.debug("set executable {filename}".format(filename = mapped.get("dst")))
                                    Path(mapped.get("dst")).chmod(0o770)
                        else:
                            Path.mkdir(Path(mapped.get("dst")), parents = True, exist_ok = True)
                            log.debug("created directory {direc}".format(direc = mapped.get("dst")))
                        
        if index.get("dst") == None:
            log.debug("deleting {tempfile}".format(tempfile = dl))
            Path(dl).unlink()
            
    async def install_one(self, index):
        log = logging.getLogger(__name__)
        if index.get("dst") != None and not Path(index.get("dst")).parent.exists():
            Path.mkdir(Path(index.get("dst")).parent, parents = True, exist_ok = True)
            log.debug("created directory {direc}".format(direc = Path(index.get("dst")).parent))
        
        dl = index.get("dst") != None and index.get("dst") or mktemp()

        log.info("installing {url}".format(url = index.get(platform.machine())))
        async with aiofiles.open(dl, 'wb') as f:
            async with aiohttp.ClientSession() as session:
                async with session.get(index.get(platform.machine()), allow_redirects = True) as r:
                    await f.write(await r.content.read())                
                    log.debug("wrote {filename}".format(filename = dl))
                    await self.extract_archive(index, dl)
                        
    async def install_all(self):
        log = logging.getLogger(__name__)
        log.info("installing container runtimes")
        log.debug("""
            note: compressed archive extraction is one problem that python isn't any
            good at solving. Please give this a few moments to finish, it won't take
            too long.
            """)
        async with asyncio.TaskGroup() as tg:
            await asyncio.gather(*[tg.create_task(self.install_one(index)) for index in self._packages])     
        log.info("installation complete")
