import asyncio
import stat
import logging
import errno
import pyfuse3
import pyfuse3.asyncio

"""
ALong with the volume driver and an HTTP client, this prition is responsible
for setting up FUSE
"""

class fuse_dav_filesystem(LoggingMixIn, Operations):
    def __init__(self):
        super(TestFs, self).__init__()
        self.hello_name = b"message"
        self.hello_inode = pyfuse3.ROOT_INODE+1
        self.hello_data = b"hello world\n"

    async def getattr(self, inode, ctx=None):
        entry = pyfuse3.EntryAttributes()
        if inode == pyfuse3.ROOT_INODE:
            entry.st_mode = (stat.S_IFDIR | 0o755)
            entry.st_size = 0
        elif inode == self.hello_inode:
            entry.st_mode = (stat.S_IFREG | 0o644)
            entry.st_size = len(self.hello_data)
        else:
            raise pyfuse3.FUSEError(errno.ENOENT)

        stamp = int(1438467123.985654 * 1e9)
        entry.st_atime_ns = stamp
        entry.st_ctime_ns = stamp
        entry.st_mtime_ns = stamp
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode

        return entry

    async def lookup(self, parent_inode, name, ctx=None):
        if parent_inode != pyfuse3.ROOT_INODE or name != self.hello_name:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return await self.getattr(self.hello_inode)

    async def opendir(self, inode, ctx):
        if inode != pyfuse3.ROOT_INODE:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return inode

    async def readdir(self, fh, start_id, token):
        assert fh == pyfuse3.ROOT_INODE

        # only one entry
        if start_id == 0:
            pyfuse3.readdir_reply(
                token, self.hello_name, await self.getattr(self.hello_inode), 1)
        return

    async def setxattr(self, inode, name, value, ctx):
        if inode != pyfuse3.ROOT_INODE or name != b'command':
            raise pyfuse3.FUSEError(errno.ENOTSUP)

        if value == b'terminate':
            pyfuse3.terminate()
        else:
            raise pyfuse3.FUSEError(errno.EINVAL)

    async def open(self, inode, flags, ctx):
        if inode != self.hello_inode:
            raise pyfuse3.FUSEError(errno.ENOENT)
        if flags & os.O_RDWR or flags & os.O_WRONLY:
            raise pyfuse3.FUSEError(errno.EACCES)
        return pyfuse3.FileInfo(fh=inode)

    async def read(self, fh, off, size):
        assert fh == self.hello_inode
        return self.hello_data[off:off+size]

