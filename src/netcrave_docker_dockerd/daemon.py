# IAmPaigeAT (paige@paige.bio) 2023

from pathlib import Path
import subprocess
import asyncio
from netcrave_docker_dockerd.setup_environment import setup_environment, setup_compose
from netcrave_docker_util.cmd import cmd_async
from netcrave_docker_util.lazy import swallow, swallow_async
import logging 
import signal 
import traceback 
from netcrave_docker_dockerd.driver import internal_network_driver
import sys 
from queue import Queue

class service():
    def __init__(self):
        self.stdoutHandler = logging.StreamHandler(stream=sys.stdout)
        signal.signal(signal.SIGINT, self.sigint)
        self.log = logging.getLogger(__name__)
        
    async def _run_internal_driver(self):
        await internal_network_driver()
        
    async def _run_dockerd(self):
        await cmd_async(
            "/opt/netcrave/bin/dockerd", 
            "--config-file", 
            "/etc/netcrave/_netcrave.json")
        
    async def _run_containerd(self):
        await cmd_async(
            "/opt/netcrave/bin/containerd", 
            "--root", 
            "/srv/_netcrave/containerd", 
            "--address", 
            "/run/_netcrave/sock.containerd")
        
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
                
    async def cleanup(self):       
        self.log.critical("please wait: attempting to shutdown cleanly...")
        await swallow_async(lambda: cmd_async("umount", "/mnt/_netcrave/docker-compose.yml"))
        await swallow_async(lambda: cmd_async("umount", "/mnt/_netcrave/.env"))
        await swallow_async(lambda: cmd_async("umount", "/mnt/_netcrave/docker"))
        await swallow_async(lambda: Path("/mnt/_netcrave/.env").unlink())
        await swallow_async(lambda: Path("/mnt/_netcrave/docker-compose.yml").unlink())
        await swallow_async(lambda: Path("/mnt/_netcrave/docker").rmdir())
        await swallow_async(lambda: self._ndb.close())
        
    def sigint(self, sig, frame):
        [index.cancel() for index in asyncio.all_tasks()]
        
    async def start(self):
        while True:
            try:
                self.log.debug("starting daemon, debugging is enabled")
                sockets, self._ca, self._ndb = await setup_environment()
                self._dockerd_sock, self._containerd_sock = sockets
                self.log.info("configuration initialized and loaded")
                self.log.info("starting daemons")                
                async with asyncio.TaskGroup() as tg:
                    await asyncio.gather(
                        tg.create_task(self._run_internal_driver()),
                        tg.create_task(self._run_containerd()),
                        tg.create_task(self._run_dockerd()))
            except asyncio.CancelledError as ex:
                self.log.critical("events cancelled {}",format(ex))
                await self.cleanup()
                raise
            except Exception as ex:
                self.log.critical("Caught non-recoverable error in early startup {ex} {stacktrace}".format(
                    ex = ex, 
                    stacktrace = "".join(
                        traceback.format_exception(ex))))
                [index.cancel() for index in asyncio.all_tasks()]
                await self.cleanup()
            break
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
            async with open("/etc/systemd/system/netcrave-dockerd-daemon.service", 'w') as file:
                file.write(systemd_script)
            
            result = await cmd("/usr/bin/env", "systemctl", "daemon-reload")
            
            if result.returncode != 0:
                Path("/etc/systemd/system/netcrave-dockerd-daemon.service").unlink()
                raise Exception("failed to reload systemd")
        else:
            raise Exception("service already installed")
