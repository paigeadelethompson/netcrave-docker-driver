# IAmPaigeAT (paige@paige.bio) 2023

from pathlib import Path
import subprocess
import asyncio
from threading import Thread
from netcrave_docker_dockerd.setup_environment import setup_environment, setup_compose
from netcrave_docker_util.cmd import cmd
from netcrave_docker_util.lazy import swallow
import logging 
import signal 
import traceback 
from netcrave_docker_dockerd.driver import oci_network_driver
import sys 
from queue import Queue
import concurrent.futures

class service():
    def __init__(self):
        self.stdoutHandler = logging.StreamHandler(stream=sys.stdout)
        signal.signal(signal.SIGINT, self.sigint)
        self.log = logging.getLogger(__name__)
        
    def _run_internal_driver(self):
        oci_network_driver()
        
    def _run_dockerd(self):
        cmd(["/opt/netcrave/bin/dockerd", "--config-file", "/etc/netcrave/_netcrave.json"])
    
    def _run_containerd(self):
        cmd(["/opt/netcrave/bin/containerd", "--root", "/opt/netcrave", "--address", "/run/_netcrave/sock.containerd"])
    
    async def _dockerd_post_start(self):        
        if len([index for index in self._proj.client.images() if len([
            index2 for index2 in index.get("RepoTags") if index2.startswith("netcrave")]) > 0]) == 0:
            self._proj.build(["netcrave-image", "netcrave-docker-image"])
        
        certificate_volumes = [self._proj.volumes.volumes.get(
            index) for index in self._proj.volumes.volumes.keys() if index.endswith("_ssl") 
            and self._proj.volumes.volumes.get(index).exists()]
        
        if len(certificate_volumes) == 0:
            self._proj.up(["cockroach-copy-certs"])
            self._proj.up(["cockroach"])
            self._proj.up(["cockroach-databases"])
            self._proj.down(False, False)
            self._proj.up([
                "cockroach",
                "ipam", 
                "ifconfig", 
                "haproxycfg", 
                "cerfiticatemgr", 
                "dnsd", 
                "icap", 
                "haproxy", 
                "squid", 
                "fluentd",
                "davfs",
                "acme",
                "powerdns",
                "frr-netcrave",
                "frr-docker"], start = False)
                
    def cleanup(self):       
        self.log.critical("please wait: attempting to shutdown cleanly...")
        swallow(lambda: cmd(["umount", "/mnt/_netcrave/docker-compose.yml"]))
        swallow(lambda: cmd(["umount", "/mnt/_netcrave/.env"]))
        swallow(lambda: cmd(["umount", "/mnt/_netcrave/docker"]))
        swallow(lambda: Path("/mnt/_netcrave/.env").unlink())
        swallow(lambda: Path("/mnt/_netcrave/docker-compose.yml").unlink())
        swallow(lambda: Path("/mnt/_netcrave/docker").rmdir())
        swallow(lambda: self._ndb.close())
        self.log.critical("finished")
        
    def sigint(self, sig, frame):
        self.cleanup()
        
    async def start(self):
        try:
            self.log.debug("starting daemon, debugging is enabled")
            sockets, self._ca, self._ndb = await setup_environment()
            self._dockerd_sock, self._containerd_sock = sockets
            #self._dockerd_post_start()     
            
#             executor = concurrent.futures.ThreadPoolExecutor(max_workers = 8)
#             event_loop = asyncio.get_event_loop()
#             for index in [asyncio.create_task(self._run_containerd()),
#              asyncio.create_task(self._run_dockerd()),
#             asyncio.create_task(self._run_internal_driver())]:
#                 event_loop.run_in_executor(executor, index)
#         
        except Exception as ex:
            self.log.critical("Caught non-recoverable error in early startup {ex} {stacktrace}".format(
                ex = ex, 
                stacktrace = "".join(
                    traceback.format_exception(ex))))
            self.cleanup()
    
    async def create_service(self):
        systemd_script = """
            [Unit]
            Description="Netcrave Container Service"
            
            StartLimitIntervalSec=60000

            [Service]
            Type=notify
            ExecStartPre=/usr/bin/env netcrave-dockerd-environment
            ExecStart=/usr/bin/env netcrave-dockerd-daemon
            Restart=never

            [Install]
            WantedBy=multi-user.target
            """
            
        if not Path("/etc/systemd/system/netcrave-dockerd-daemon.service").exists():
            with open("/etc/systemd/system/netcrave-dockerd-daemon.service", 'w') as file:
                file.write(systemd_script)
            
            result = cmd(["/usr/bin/env", "systemctl", "daemon-reload"])
            
            if result.returncode != 0:
                Path("/etc/systemd/system/netcrave-dockerd-daemon.service").unlink()
                raise Exception("failed to reload systemd")
        else:
            raise Exception("service already installed")
