# IAmPaigeAT (paige@paige.bio) 2023
import logging
import asyncio.subprocess
import subprocess
import os, tempfile
from os import O_NONBLOCK
import itertools
from pathlib import Path
import sys
import time
import datetime
import logging
import os
import asyncio
from netcrave_docker_util.exception import unknown

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
main_logger = logging.getLogger('__main__')
main_logger.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
try:
    import colorlog  # `pip install colorlog` for extra goodies.

    stream_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)-6s %(green)s%(module)s %(cyan)s%(funcName)s %(white)s%(message)s',
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

class io_proxy():
    def __init__(self, *args, **kwargs):
        self._fd_out_stdout, self._fd_in_stdout = os.pipe2(O_NONBLOCK)
        self._fd_out_stderr, self._fd_in_stderr = os.pipe2(O_NONBLOCK)
        self._pipe_in_stdout = os.fdopen(self._fd_in_stdout, 'w')
        self._pipe_out_stdout = os.fdopen(self._fd_out_stdout, 'r')
        self._pipe_in_stderr = os.fdopen(self._fd_in_stderr, 'w')
        self._pipe_out_stderr = os.fdopen(self._fd_out_stderr, 'r')
    async def _background_log(self, stream, fd, proc):
        log = logging.getLogger(__name__)
        try:
            while Path("/proc/{pid}".format(pid = proc.pid)).exists():
                try:
                    for index in stream:
                        log.debug(
                            "[{pid} {buf} inner] {msg}".format(
                                msg = index.rstrip(), 
                                pid = proc.pid, 
                                buf = (fd == self._fd_out_stdout and "stdout" or "stderr")))
                except Exception as ex:
                    log.warning(
                        "[{pid} {buf} inner] {msg}".format(
                            msg = ex, 
                            pid = proc.pid, 
                            buf = (fd == self._fd_out_stdout and "stdout" or "stderr")))
                await asyncio.sleep(1)
            for index in stream:
                log.debug(
                    "[{pid} {buf} outer] {msg}".format(
                        msg = index.rstrip(), 
                        pid = proc.pid, 
                        buf = (fd == self._fd_out_stdout and "stdout" or "stderr")))
        except Exception as ex:
            log.warning(
                "[{pid} {buf} outer] {msg}".format(
                    msg = ex, 
                    pid = proc.pid, 
                    buf = (fd == self._fd_out_stdout and "stdout" or "stderr")))
        
    def stderr(self):
        return self._pipe_in_stderr
    def stdout(self):
        return self._pipe_in_stdout
    async def tasks(self, proc):
        log = logging.getLogger(__name__)
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._background_log(self._pipe_out_stdout, self._fd_out_stdout, proc))
                tg.create_task(self._background_log(self._pipe_out_stderr, self._fd_out_stderr, proc))
                return tg
        except Exception as ex:
            log.critical("[{pid}] {msg}".format(msg = ex, pid = proc.pid))
            raise unknown(ex)

async def process_cmd(proc_coro, prx):
    log = logging.getLogger(__name__)
    log.debug("processing subprocess command async")
    try:
        proc = proc_coro
        async with asyncio.TaskGroup() as tg:
            tg.create_task(proc.wait())
            tg.create_task(prx.tasks(proc))
            return tg
    except Exception as ex:
        log.critical("{msg}".format(msg = ex))
        raise unknown(ex)


async def cmd_async(*args, **kwargs):
    log = logging.getLogger(__name__)
    log.info("executing async command {}".format([*args]))
    try:
        prx = io_proxy()
        proc_coro = await asyncio.subprocess.create_subprocess_exec(*args, stdout = prx.stdout(), stderr=prx.stderr())
        await asyncio.gather(process_cmd(proc_coro, prx))
    except Exception as ex:
        log.critical("['async {cmd}' ] {msg}".format(msg = ex, cmd = " ".join([*args])))
        raise unknown(ex)
