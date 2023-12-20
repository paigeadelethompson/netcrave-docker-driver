import datetime
import logging
import os
import sys
import asyncio
import argparse
from netcrave_docker_dockerd.daemon import service
from netcrave_docker_dockerd.runtime_installer import installer
from netcrave_docker_util.log import configure_logger_for_module


module_logger, main_logger, console_handler = configure_logger_for_module(__name__)

def daemon():
    svc = service()
    try:
        asyncio.get_event_loop().run_until_complete(svc.start())
    except asyncio.CancelledError:
        logging.getLogger(__name__).info("Tasks aborted, exiting")
        try:
            svc.cleanup()
        except Exception as ex:
            logging.getLogger(__name__).error(ex)
            sys.exit(1)

def install():
    try:
        parser = argparse.ArgumentParser(
            prog='netcrave-docker-install',
            description='Install various or all components of netcrave-docker')
        parser.add_argument(
            '-r',
            '--runtimes',
            action=argparse.BooleanOptionalAction)
        parser.add_argument(
            '-s',
            '--systemd',
            action=argparse.BooleanOptionalAction)
        args = parser.parse_args()
        if args.runtimes:
            asyncio.get_event_loop().run_until_complete(installer().install_all())
        if args.systemd:
            asyncio.get_event_loop().run_until_complete(service().create_service())
    except Exception as ex:
        logging.getLogger(__name__).critical("An error occurred {}".format(ex))
