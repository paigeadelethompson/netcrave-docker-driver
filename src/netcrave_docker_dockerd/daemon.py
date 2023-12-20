# IAmPaigeAT (paige@paige.bio) 2023

from pathlib import Path
import subprocess
import asyncio
from netcrave_docker_dockerd.setup_environment import setup_environment, setup_compose
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
        self.log = logging.getLogger(__name__)
        self._docker_dependency = asyncio.Lock()
        self._docker_network_driver_dependency = asyncio.Lock()

    async def _run_internal_driver(self):
        await internal_driver.internal_network_driver(
            cls=internal_driver,
            path="/srv/netcrave/_netcrave/state/plugins",
            sock_name="netcfg.sock",
            sem=self._docker_dependency)

    async def _run_dockerd(self):
        await cmd_async(
            "/opt/netcrave/bin/dockerd",
            "--config-file",
            "/etc/netcrave/_netcrave.json")

    async def _run_containerd(self):
        await cmd_async(
            "/opt/netcrave/bin/containerd",
            "--root",
            "/srv/netcrave/_netcrave/containerd",
            "--address",
            "/run/netcrave/_netcrave/sock.containerd")

    async def _wait_for_docker_daemon(self):
        while True:
            try:
                docker.client.DockerClient(
                    "unix:///run/netcrave/_netcrave/sock.dockerd")
                self.log.info("docker is online, releasing dependency lock")
                self._docker_dependency.release()
                return
            except DockerException:
                self.log.warn("waiting for docker daemon to come online")
            await asyncio.sleep(1)

    async def _wait_for_docker_network_driver(self):
        while True:
            try:
                pass
                # docker.client.DockerClient("unix:///run/_netcrave/sock.dockerd")
                # self.log.info("docker is online, releasing dependency lock")
                # self._docker_dependency.release()
                # return
            except DockerException:
                self.log.warn("waiting for docker daemon to come online")
            await asyncio.sleep(1)

    async def _dockerd_post_start(self):
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
            self.log.error("compose failed {}".format(ex))

    def cleanup(self):
        self.log.critical("please wait: attempting to shutdown cleanly...")
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

        if self._ndb is not None:
            self._ndb.close()

    def sigint(self, sig, frame):
        [index.cancel() for index in asyncio.all_tasks()]

    async def start(self):
        while True:
            try:
                self.log.debug("starting daemon, debugging is enabled")
                self._ca, self._ndb = await setup_environment()
                self.log.info("configuration initialized and loaded")
                self.log.info("starting daemons")
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
                self.log.critical("events cancelled {}", format(ex))
                raise
            except Exception as ex:
                self.log.critical(
                    "Caught non-recoverable error in early startup {ex} {stacktrace}".format(
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

            result = await cmd("/usr/bin/env", "systemctl", "daemon-reload")

            if result.returncode != 0:
                Path("/etc/systemd/system/netcrave-dockerd-daemon.service").unlink()
                raise Exception("failed to reload systemd")
        else:
            raise Exception("service already installed")
