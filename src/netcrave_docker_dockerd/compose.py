# IAmPaigeAT (paige@paige.bio) 2023

from compose.cli.command import get_project
from compose.config import load as compose_config_load
from compose.config.config import ConfigDetails, ConfigFile, Environment
from compose.config.config import yaml
import importlib.resources as resources
import netcrave_compose
import netcrave_compose.docker
from pathlib import Path
from netcrave_docker_dockerd.netcrave_dot_env import get as get_environment
from netcrave_docker_util.cmd import cmd_async
import aiofiles
import logging


async def compose_from_config_directory():
    return "/etc/netcrave/docker-compose.yml"


def default_compose():
    return Path(next((
        index for index in resources.files(
            netcrave_compose).iterdir()
        if str(index).endswith("docker-compose.yml"))))


async def mount_build_context(context_path):
    await cmd_async("mount", "-o", "bind,ro", context_path, "/mnt/_netcrave/docker")


async def get_compose():
    log = logging.getLogger(__name__)
    try:
        Path("/mnt/_netcrave/docker").mkdir(parents=True, exist_ok=True)
        Path("/mnt/_netcrave/.env").touch()
        Path("/mnt/_netcrave/docker-compose.yml").touch()
        dockerfile_path = default_compose().parent / Path("docker")
        await cmd_async("mount", "-o", "bind,ro", "/etc/netcrave/_netcrave.dotenv", "/mnt/_netcrave/.env")
        await cmd_async("mount", "-o", "bind,ro", dockerfile_path, "/mnt/_netcrave/docker")

        if Path(await compose_from_config_directory()).exists():
            await cmd_async("mount", "-o", "bind,ro", "/etc/netcrave/docker-compose.yml", "/mnt/_netcrave/docker-compose.yml")
            e = Environment(
                get_environment())
            e["DOCKER_HOST"] = "unix:///run/netcrave/_netcrave/sock.dockerd"

            return get_project(
                "/mnt/_netcrave",
                interpolate=True,
                environment=e)

        await cmd_async("mount", "-o", "bind,ro", default_compose(), "/mnt/_netcrave/docker-compose.yml")
        cfg = ConfigFile.from_filename("/mnt/_netcrave/docker-compose.yml")
        load_test = compose_config_load(
            ConfigDetails(
                ".",
                [cfg],
                Environment(get_environment())),
            interpolate=True)

        async with aiofiles.open("/etc/netcrave/docker-compose.yml", "+wb") as new_file:
            await new_file.write(bytes(yaml.dump(cfg.config), 'utf-8'))
            await cmd_async("umount", "/mnt/_netcrave/docker-compose.yml")
            await cmd_async("mount", "-o", "bind,ro", "/etc/netcrave/docker-compose.yml", "/mnt/_netcrave/docker-compose.yml")

        e = Environment(
            get_environment())
        e["DOCKER_HOST"] = "unix:///run/netcrave/_netcrave/sock.dockerd"

        return get_project(
            "/mnt/_netcrave",
            interpolate=True,
            environment=e)

    except Exception:
        log.critical(
            """
            This could be bad, please report a bug if you cannot troubleshoot this error:
            If you know what is causing the issue, then you may be able to work around by
            supplying a netcrave-compose.yml of your own in /etc/netcrave/
            """)
        raise
