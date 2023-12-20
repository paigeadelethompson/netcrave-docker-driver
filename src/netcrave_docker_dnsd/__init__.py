# IAmPaigeAT (paige@paige.bio) 2023

import asyncio
import logging
import sys
from netcrave_docker_dnsd.daemon import dns_daemon
from netcrave_docker_util.log import configure_logger_for_module


module_logger, main_logger, console_handler = configure_logger_for_module(
    __name__)


def daemon():
    dnsd = dns_daemon()
    try:
        asyncio.get_event_loop().run_until_complete(dnsd.run())
    except asyncio.CancelledError:
        logging.getLogger(__name__).info("Tasks aborted, exiting")
        sys.exit(1)
