# IAmPaigeAT (paige@paige.bio) 2023

from pathlib import Path
import subprocess
import asyncio
import os
import logging
import signal
import traceback
import sys
import docker
from docker.errors import DockerException
from netcrave_docker_util.ndb import network_database
from netcrave_docker_util.cmd import cmd_async
from netcrave_docker_dockerd.driver import internal_driver
from netcrave_docker_dockerd.setup_environment import (setup_environment,
                                                       get_id,
                                                       setup_compose,
                                                       change_netns,
                                                       restore_default_netns)

class service():
    def __init__(self):
        self.stdoutHandler = logging.StreamHandler(stream=sys.stdout)
        signal.signal(signal.SIGINT, self.sigint)
        self._docker_dependency = asyncio.Lock()

    async def _run_internal_driver(self):
        log = logging.getLogger(__name__)
        id = await get_id("_netcrave")
        gid = await get_id("_netcrave", "/etc/group")
        pid = os.fork()

        if pid == 0:
            # os.setgid(gid)
            # os.setuid(id)
            # assert os.getuid() == id
            # assert os.getgid() == gid # XXX need root to modify interfaces RTNL, priv

            log.debug("forked and setuid/gid to uid: {} gid: {} pid: {}".format(
                os.getuid(),
                os.getgid(),
                pid))

            loop = asyncio.new_event_loop()
            loop.run_until_complete(internal_driver.internal_network_driver(
                internal_driver,
                "/run/docker/plugins/",
                "_netcrave.sock"))

        else:
            # XXX TODO this call to get_event_loop is different from the one in the parent if statement,
            # rather it returns a different loop from the child after fork(), but this parent has to remain
            # active otherwise the child process will close when this async task finishes, for now just
            # wait unconditionally forever
            while asyncio.get_event_loop().is_running():
                await asyncio.sleep(sys.maxsize)

    async def _run_dockerd(self):
        assert os.getuid() == 0
        await change_netns() 


        await cmd_async(
            "/opt/netcrave/bin/dockerd",
            "--config-file",
            "/etc/netcrave/_netcrave.json")

    async def _run_containerd(self):
        assert os.getuid() == 0
        await change_netns()

        await cmd_async(
            "/opt/netcrave/bin/containerd",
            "--root",
            "/srv/netcrave/_netcrave/bin/containerd",
            "--address",
            "/run/netcrave/_netcrave/sock.containerd")

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

    # async def _dockerd_post_start(self):
    #     log = logging.getLogger(__name__)
    #     try:
    #         await self._docker_dependency.acquire()
    #         self._docker_dependency.release()
    #         id = await get_id("_netcrave")
    #         gid = await get_id("_netcrave", "/etc/group")
    #         pid = os.fork()

    #         if pid != 0:
    #             pass
    #         else:
    #             os.setgid(gid)
    #             os.setuid(id)
    #             assert os.getuid() == id
    #             assert os.getgid() == gid

    #             log.debug("forked and setuid/gid to uid: {} gid: {} pid: {}".format(
    #                 os.getuid(),
    #                 os.getgid(),
    #                 pid))

    #             loop = asyncio.new_event_loop()
    #            loop.run_until_complete()


    #         self._proj = await setup_compose()

    #         if len([index for index in self._proj.client.images() if len(
    #                 [index2 for index2 in index.get("RepoTags") if index2.startswith("netcrave")]) > 0]) == 0:

    #             self._proj.build(["netcrave-image"])
    #             self._proj.build(["netcrave-docker-image"])

    #         certificate_volumes = [
    #             self._proj.volumes.volumes.get(index)
    #             for index in self._proj.volumes.volumes.keys()
    #             if index.endswith("_ssl") and self._proj.volumes.volumes.get(index).exists()]

    #         if len(certificate_volumes) == 0:
    #             self._proj.up(["cockroach-copy-certs"])
    #             self._proj.up(["cockroach"])
    #             self._proj.up(["cockroach-databases"])
    #             self._proj.down(False, False)
    #             self._proj.up([
    #                 "cockroach",
    #                 "ipam",
    #                 "ifconfig",
    #                 "haproxycfg",
    #                 "cerfiticatemgr",
    #                 "dnsd",
    #                 "icap",
    #                 "haproxy",
    #                 "squid",
    #                 "fluentd",
    #                 "davfs",
    #                 "acme",
    #                 "powerdns",
    #                 "frr-netcrave",
    #                 "frr-docker"], start=False)
    #     except Exception as ex:
    #         log.error("compose failed {}".format(ex))

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

        #network_database().__del__() # XXX Singleton which keeps handle open to NDB

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
                        # tg.create_task(self._dockerd_post_start()),
                        tg.create_task(self._wait_for_docker_daemon()))

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
