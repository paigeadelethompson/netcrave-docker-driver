import os
import glob
import socket
import errno
import time
import six

from haproxyadmin.frontend import Frontend
from haproxyadmin.backend import Backend
from haproxyadmin.utils import (is_unix_socket, cmd_across_all_procs, converter,
                                calculate, isint, should_die, check_command,
                                check_output, compare_values, connected_socket)
from haproxyadmin.exceptions import CommandFailed
from haproxyadmin import HAProxy
from haproxyadmin.internal.haproxy import _HAProxyProcess
from haproxyadmin.utils import (info2dict, stat2dict)
from haproxyadmin.exceptions import (SocketTransportError, SocketTimeout,
                                     SocketConnectionError)
from haproxyadmin.internal.frontend import _Frontend
from haproxyadmin.internal.backend import _Backend

class HAProxyProcessCustom(_HAProxyProcess):
    def __init__(self):
        raise NotImplementedError()

    def command(self, command, full_output=False):
        raise NotImplementedError()

    def proc_info(self):
        raise NotImplementedError()

    def stats(self, iid=-1, obj_type=-1, sid=-1):
        raise NotImplementedError()

    def metric(self, name):
        raise NotImplementedError()

    def backends_stats(self, iid=-1):
        raise NotImplementedError()
    
    def frontends_stats(self, iid=-1):
        raise NotImplementedError()

    def servers_stats(self, backend, iid=-1, sid=-1):
       raise NotImplementedError()

    def backends(self, name=None):
        raise NotImplementedError()
    
    def frontends(self, name=None):
        raise NotImplementedError()
    
class HAProxyCustom(HAProxy): 
    def __init__(self):
        self._hap_processes.append(
                _HAProxyProcessCustom()
            )
