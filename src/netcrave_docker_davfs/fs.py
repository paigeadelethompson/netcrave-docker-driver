import stat
import errno
import pyfuse3
import pyfuse3.asyncio


class fuse_dav_filesystem(LoggingMixIn, Operations):
    def __init__(self):
        raise NotImplementedError()

    async def getattr(self, inode, ctx=None):
        entry = pyfuse3.EntryAttributes()
        raise NotImplementedError()

    async def lookup(self, parent_inode, name, ctx=None):
        if parent_inode != pyfuse3.ROOT_INODE:
            raise pyfuse3.FUSEError(errno.ENOENT)
        raise NotImplementedError()

    async def opendir(self, inode, ctx):
        raise NotImplementedError()

    async def readdir(self, fh, start_id, token):
        raise NotImplementedError()

    async def setxattr(self, inode, name, value, ctx):
        raise NotImplementedError()

    async def open(self, inode, flags, ctx):
        if flags & os.O_RDWR or flags & os.O_WRONLY:
            raise pyfuse3.FUSEError(errno.EACCES)
        raise NotImplementedError()

    async def read(self, fh, off, size):
        raise NotImplementedError()
