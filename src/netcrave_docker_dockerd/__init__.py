import datetime
import logging
import os, sys
import asyncio
import argparse
from netcrave_docker_dockerd.daemon import service
from netcrave_docker_dockerd.runtime_installer import installer

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
main_logger = logging.getLogger('__main__')
main_logger.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

try:
    import colorlog

    stream_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)s %(green)s%(module)s %(cyan)s%(funcName)s %(white)s%(message)s',
        "%H:%M:%S",
        log_colors={
            'DEBUG': 'blue',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
            'EXCEPTION': 'bold_red',
        })
except ImportError:
    stream_formatter = logging.Formatter('%(levelname)s %(module)s %(funcName)s %(message)s')
console_handler.setFormatter(stream_formatter)

package_timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
if os.path.isdir('logs'):
    file_handler = logging.FileHandler(
        os.path.join('logs', '{}_{}.log'.format(__name__, package_timestamp)), mode='a')
    file_handler.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s %(module)s %(name)s %(message)s'))
    module_logger.addHandler(file_handler)
    main_logger.addHandler(file_handler)

module_logger.addHandler(console_handler)
main_logger.addHandler(console_handler)

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
            prog = 'netcrave-docker-install',
            description = 'Install various or all components of netcrave-docker')
        parser.add_argument(
            '-r', 
            '--runtimes',
            action = argparse.BooleanOptionalAction)
        parser.add_argument(
            '-s', 
            '--systemd',
            action = argparse.BooleanOptionalAction)
        args = parser.parse_args()
        if args.runtimes:
            asyncio.get_event_loop().run_until_complete(installer().install_all())
        if args.systemd:
            asyncio.get_event_loop().run_until_complete(service().create_service())
    except Exception as ex:
        logging.getLogger(__name__).critical("An error occurred {}".format(ex))
