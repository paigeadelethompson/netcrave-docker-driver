from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from webdav3.client import Client

class fuse_dav_filesystem(LoggingMixIn, Operations):
    def __init__(self, remote):
        if remote == "certificate":
            self.remote = "2001:db8:aaaa:aabe:192:0:0:42"
        else:
            raise NotImplementedError()
        
    def chmod(self, path, mode):
        raise NotImplementedError()

    def chown(self, path, uid, gid):
        raise NotImplementedError()

    def create(self, path, mode):
        raise NotImplementedError()

    def getattr(self, path, fh = None):
        raise NotImplementedError()

    def getxattr(self, path, name, position = 0):
        raise NotImplementedError()

    def listxattr(self, path):
        raise NotImplementedError()

    def mkdir(self, path, mode):
        raise NotImplementedError()

    def open(self, path, flags):
        raise NotImplementedError()

    def read(self, path, size, offset, fh):
        raise NotImplementedError()

    def readdir(self, path, fh):
        raise NotImplementedError()

    def readlink(self, path):
        raise NotImplementedError()

    def removexattr(self, path, name):
        raise NotImplementedError()

    def rename(self, old, new):
        raise NotImplementedError()

    def rmdir(self, path):
        raise NotImplementedError()

    def setxattr(self, path, name, value, options, position = 0):
        raise NotImplementedError()

    def statfs(self, path):
        raise NotImplementedError()

    def symlink(self, target, source):
        raise NotImplementedError()

    def truncate(self, path, length, fh = None):
        raise NotImplementedError()

    def unlink(self, path):
        raise NotImplementedError()

    def utimens(self, path, times = None):
        raise NotImplementedError()

    def write(self, path, data, offset, fh):
        raise NotImplementedError()
