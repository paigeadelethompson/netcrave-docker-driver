# IAmPaigeAT (paige@paige.bio) 2023

from pathlib import Path
import subprocess
import asyncio
import aiofiles
import os
from netcrave_docker_dockerd.setup_environment import setup_environment, setup_compose
from netcrave_docker_util.ndb import network_database
from netcrave_docker_util.cmd import cmd_async
import logging
import signal
import traceback
from netcrave_docker_dockerd.driver import internal_driver
import sys
import docker
from docker.errors import DockerException

class service():
    def __init__(self):
        self.stdoutHandler = logging.StreamHandler(stream=sys.stdout)
        signal.signal(signal.SIGINT, self.sigint)
        self._docker_dependency = asyncio.Lock()
        self._docker_network_driver_dependency = asyncio.Lock()

    async def _run_internal_driver(self):
        await internal_driver.internal_network_driver(
            cls=internal_driver,
            path="/run/docker/plugins",
            sock_name="_netcrave.sock",
            sem=self._docker_dependency)

    async def _run_dockerd(self):
        r, w = os.pipe2(os.O_NONBLOCK)
        with open(Path("/proc/{pid}/fd/{fd}".format(pid=os.getpid(), fd=w)), "wb") as script:
            script.write("""#!/usr/bin/env bash
                /usr/bin/env ip netns exec _netcrave        \
                bash -c "cgroupfs-mount ;                   \
                /opt/netcrave/bin/dockerd                   \
                --config-file /etc/netcrave/_netcrave.json  \
                "                                           \
                exit ; true
                """.encode("utf-8", "strict"))
            script.flush()
            await cmd_async("/usr/bin/env",
                            "bash",
                            "/proc/{pid}/fd/{fd}".format(pid=os.getpid(), fd=r))

    async def _run_containerd(self):
        r, w = os.pipe2(os.O_NONBLOCK)
        with open(Path("/proc/{pid}/fd/{fd}".format(pid=os.getpid(), fd=w)), "wb") as script:
            script.write("""#!/usr/bin/env bash
                /usr/bin/env ip netns exec _netcrave        \
                bash -c "cgroupfs-mount ;                   \
                /opt/netcrave/bin/containerd                \
                --root /srv/netcrave/_netcrave/containerd   \
                --address                                   \
                /run/netcrave/_netcrave/sock.containerd     \
                "                                           \
                exit ; true
                """.encode("utf-8", "strict"))
            script.flush()
            await cmd_async("/usr/bin/env",
                            "bash",
                            "/proc/{pid}/fd/{fd}".format(pid=os.getpid(), fd=r))        
        
    async def _wait_for_docker_daemon(self):
        log = logging.getLogger(__name__)
        while True:
            try:
                docker.client.DockerClient(
                    "unix:///run/netcrave/_netcrave/sock.dockerd")
                log.info("docker is online, releasing dependency lock")
                self._docker_dependency.release()
                return
            except DockerException:
                log.warn("waiting for docker daemon to come online")
            await asyncio.sleep(1)

    async def _wait_for_docker_network_driver(self):
        log = logging.getLogger(__name__)
        while True:
            try:
                pass
                # docker.client.DockerClient("unix:///run/_netcrave/sock.dockerd")
                # self.log.info("docker is online, releasing dependency lock")
                # self._docker_dependency.release()
                # return
            except DockerException:
                log.warn("waiting for docker daemon to come online")
            await asyncio.sleep(1)

    async def _dockerd_post_start(self):
        return
        log = logging.getLogger(__name__)
        await self._docker_network_driver_dependency.acquire()
        self._docker_network_driver_dependency.release()
        self._proj = await setup_compose()
        try:
            if len([index for index in self._proj.client.images() if len(
                    [index2 for index2 in index.get("RepoTags") if index2.startswith("netcrave")]) > 0]) == 0:
                self._proj.build(["netcrave-image"])
                self._proj.build(["netcrave-docker-image"])

            certificate_volumes = [
                self._proj.volumes.volumes.get(index)
                for index in self._proj.volumes.volumes.keys()
                if index.endswith("_ssl") and self._proj.volumes.volumes.get(
                    index).exists()]

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
                    "frr-docker"], start=False)
        except Exception as ex:
            log.error("compose failed {}".format(ex))

    def cleanup(self):
        log = logging.getLogger(__name__)
        log.critical("please wait: attempting to shutdown cleanly...")
        subprocess.run(["umount", "/mnt/_netcrave/docker-compose.yml"])
        subprocess.run(["umount", "/mnt/_netcrave/.env"])
        subprocess.run(["umount", "/mnt/_netcrave/docker"])
        Path("/mnt/_netcrave/.env").unlink(missing_ok=True)
        Path("/mnt/_netcrave/docker-compose.yml").unlink(missing_ok=True)

        if Path("/mnt/_netcrave/docker").exists():
            try:
                Path("/mnt/_netcrave/docker").rmdir()
            except BaseException:
                pass
            
        network_database().__del__()
            
    def sigint(self, sig, frame):
        [index.cancel() for index in asyncio.all_tasks()]

    async def start(self):
        log = logging.getLogger(__name__)
        while True:
            try:
                log.debug("starting daemon, debugging is enabled")
                await setup_environment()
                log.info("configuration initialized and loaded")
                log.info("starting daemons")
                
                async with asyncio.TaskGroup() as tg:
                    await self._docker_dependency.acquire()
                    await asyncio.gather(
                        tg.create_task(self._run_internal_driver()),
                        tg.create_task(self._run_containerd()),
                        tg.create_task(self._run_dockerd()),
                        tg.create_task(self._dockerd_post_start()),
                        tg.create_task(self._wait_for_docker_daemon()),
                        tg.create_task(self._wait_for_docker_network_driver()))

            except asyncio.CancelledError as ex:
                log.critical("events cancelled {}".format(ex))
                raise
            except Exception as ex:
                log.critical(
                    "Caught non-recoverable error {ex} {stacktrace}".format(
                        ex=ex, stacktrace="".join(
                            traceback.format_exception(ex))))
                [index.cancel() for index in asyncio.all_tasks()]
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

        if not Path(
                "/etc/systemd/system/netcrave-dockerd-daemon.service").exists():
            async with open("/etc/systemd/system/netcrave-dockerd-daemon.service", 'w') as file:
                file.write(systemd_script)

            result = await cmd_async("/usr/bin/env", "systemctl", "daemon-reload")

            if result.returncode != 0:
                Path("/etc/systemd/system/netcrave-dockerd-daemon.service").unlink()
                raise Exception("failed to reload systemd")
        else:
            raise Exception("service already installed")
