import asyncio
from haproxyadmin import haproxy


class haproxy_ctl():
    """
    https://pypi.org/project/haproxyadmin/
    https://haproxyadmin.readthedocs.io/en/latest/
    https://haproxyadmin.readthedocs.io/en/latest/dev/api.html#haproxyadmin-haproxy
    https://www.haproxy.com/blog/dynamic-ssl-certificate-storage-in-haproxy
    """
    def __init__(self):
        self._hap = haproxy.HAProxy(socket_dir='/run/sock.haproxy')
        pass
    
    async def run(self):
        pass
    
