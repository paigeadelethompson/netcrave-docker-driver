from compose.cli.command import get_project
from compose.config import load as compose_config_load
from compose.config.config import ConfigDetails, ConfigFile
from compose.config.config.yaml import dump
import importlib.resources as resources
import toml
import netcrave_compose
from pathlib import Path
import os

from netcrave_docker_dockerd.netcrave_dot_env import get as get_environment

def compose_from_config_directory():
    return "/etc/netcrave/netcrave-compose.yml"

def default_compose():
    Path(resources.path(netcrave_compose, "docker-compose.yml"))

def netcrave_compose():
    if Path.exists(compose_from_config_directory()):
        return get_project(
            "/etc/netcrave", 
            interpolate = True,
            environment = Environment(
                get_environment()))
    try:
        templ_path = default_compose()
        cfg = ConfigFile.from_filename("docker-compose.yml")
        for index in cfg.config.get("services"):
            if cfg.config.get("services"
                ).get(index
                ).get("build") != None:
                    if cfg.config.get("services"
                        ).get(index
                        ).get("build"
                        ).get("args") != None:
                            if cfg.config.get("services"
                                ).get(index
                                ).get("build"
                                ).get("args"
                                ).get("TEMPLATE_ROOT") != None:
                                    cfg.config["services"][index]["build"]["args"]["TEMPLATE_ROOT"] = str(Path.joinpath(
                                        templ_path.parent,
                                        cfg.config.get("services"
                                            ).get(index
                                            ).get("build"
                                            ).get("args"
                                            ).get("TEMPLATE_ROOT")))
                            if cfg.config.get("services"
                                ).get(index
                                ).get("build"
                                ).get("dockerfile") != None:
                                    cfg.config["services"][index]["build"]["dockerfile"] = str(Path.joinpath(
                                        templ_path.parent,
                                        cfg.config["services"][index]["build"]["dockerfile"]))
        
        load_test = compose_config_load(
            ConfigDetails(
                ".", 
                [cfg], 
                Environment(get_environment())), 
            interpolate = True)
        
        with open("/etc/netcrave/netcrave-compose.yml", "+wb") as new_file:
            new_file.write(dump(cfg.config))
    except Exception as ex:
        raise(Exception(
            """
            This could be bad, please report a bug if you cannot troubleshoot this error:
            If you know what is causing the issue, then you may be able to work around by 
            supplying a netcrave-compose.yml of your own in /etc/netcrave/
            {exception}
            """.format(ex)))
    
    return get_project(
        "/etc/netcrave", 
        interpolate = True,
        environment = Environment(
            get_environment()))
        
