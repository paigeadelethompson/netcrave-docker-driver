import asyncio
import logging
import sys
from netcrave_docker_ipam.http import ipam_driver
from netcrave_docker_util.log import configure_logger_for_module


module_logger, main_logger, console_handler = configure_logger_for_module(__name__)

def daemon():
    try:
        asyncio.get_event_loop().run_until_complete(filesystem_driver.internal_network_driver(cls=network_driver, 
                                                                                              path="/srv/netcrave/docker/state/plugins/",
                                                                                              sock_name="ipam.sock"))
    except asyncio.CancelledError:
        logging.getLogger(__name__).info("Tasks aborted, exiting")
        sys.exit(1)
