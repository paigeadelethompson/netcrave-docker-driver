import io
import asyncio
import threading
import logging
import asyncio.subprocess
import subprocess

log = logging.getLogger(__name__)

class io_proxy():
    def __init__(self, io, desc, *args, **kwargs):
        self._io = io
        self._desc = desc
        super(self.__class__, self).__init__(*args, **kwargs)
    def __call__(self, *args, **kwargs):
        self._io.__call__(*args)
    def fileno(self, *args, **kwargs):
        return self._desc

def cmd(*args, **kwargs):
    out = io.StringIO()
    proc = subprocess.Popen(
        *args, 
        stdout = io_proxy(io = out, desc = 1),
        stderr = io_proxy(io = out, desc = 2))
    for index in out:
        log.debug("%s: %s", proc, line.decode().rstrip())
    
async def cmd_async(*args, **kwargs):
    out = io.StringIO()
    proc = await asyncio.subprocess.create_subprocess_exec(
        *args, 
        stdout = io_proxy(io = out, desc = 1),
        stderr = io_proxy(io = out, desc = 1))
    
    for line in out:        
        log.debug("%s: %s", proc, line.decode().rstrip())
    
    await proc.wait()
