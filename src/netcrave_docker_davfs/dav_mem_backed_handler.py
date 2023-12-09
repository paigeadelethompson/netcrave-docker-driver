# IAmPaigeAT paige@paige.bio 2023

from __future__ import absolute_import
import os
import textwrap
import six
import logging
import types
import shutil
from io import StringIO
from six.moves import urllib
from pywebdav.lib.constants import COLLECTION, OBJECT
from pywebdav.lib.errors import *
from pywebdav.lib.iface import *
from pywebdav.lib.davcmd import copyone, copytree, moveone, movetree, delone, deltree
import mimetypes
import magic
import pathlib 
from datetime import datetime

class memory_backed_descriptor():
    def __str__(self): 
        return "{parent}/{path}".format(parent = self._parent.strip("/"), path = self._path.strip("/"))
    
    def __init__(self, 
                 path = "/", 
                 parent = None, 
                 data = bytes(0), 
                 mime = None,
                 init = True)
        
        self._path = path
        self._parent = parent
        self._data = data
        self._mime = (mime != mimetypes.directory
                      ) and magic.detect_from_content(data).mime_type or None
        
        if self._mime == mimetypes.directory:
            self._children = [
                memory_backed_descriptor(path = ".", 
                                         parent = self, 
                                         data = bytes([0]), 
                                         mime = mimetypes.directory), 
                memory_backed_descriptor(path = "..", 
                                         parent = parent, 
                                         data = bytes([0]), 
                                         mime = mimetypes.directory)]
    
    def size(self):
        return len(self._data)
    
    def path(self):
        return self._path
    
    def traverse(self, path, depth = 1):
        if len(path.split("/")) >= depth:
                for index in self._children:
                    if index.path() == path.split("/")[depth]:
                        return index.traverse(path, depth + 1)
        elif path.split("/")[-1] == self.path():
            return self
        else:
            raise NotImplementedError()
        
    def children(self, path = None):
        if path != None:
            return self.traverse(path)
        if self._mime == mimetypes.directory:
            return self._children
        raise NotImplementedError()
    
    def data(self, path = None):
        return self._data
            
class Resource(object):
    def __init__(self, data):
        self._data = data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for index in self._data

    def read(self, length = 0):
        return self._data
    
class FilesystemHandler(dav_interface):
    def __init__(self, fs):
        self._fs = fs
        
    def setDirectory(self, path):
        raise NotImplementedError()

    def setBaseURI(self, uri):
        raise NotImplementedError()

    def uri2local(self,uri):
        raise NotImplementedError()

    def local2uri(self,filename):
        raise NotImplementedError()


    def get_childs(self, uri, filter=None):
        self._fs.children(uri)
    
    def _get_listing(self, path)
        template = textwrap.dedent("""
            <html>
                <head><title>Directory listing for {path}</title></head>
                <body>
                    <h1>Directory listing for {path}</h1>
                    <hr>
                    <ul>
                    {items}
                    </ul>
                    <hr>
                </body>
            </html>
            """.format(path, "\n".join(['<li><a href="{index}">{index}</a></li>'.format(str(index)) for index in self.get_childs(path)])
        return template

    def get_data(self, uri, range = None):
        return Resource(self._fs.traverse(uri).data())
        
    def _get_dav_resourcetype(self,uri):
        raise NotImplementedError()

    def _get_dav_displayname(self,uri):
        raise NotImplementedError()

    def _get_dav_getcontentlength(self,uri):
        raise NotImplementedError()

    def get_lastmodified(self,uri):
        raise NotImplementedError()

    def get_creationdate(self,uri):
        raise NotImplementedError()

    def _get_dav_getcontenttype(self, uri):
        raise NotImplementedError()

    def put(self, uri, data, content_type=None):
        raise NotImplementedError()
    
    def mkcol(self,uri):
        raise NotImplementedError()

    ### ?? should we do the handler stuff for DELETE, too ?
    ### (see below)

    def rmcol(self,uri):
        raise NotImplementedError()

    def rm(self,uri):
        raise NotImplementedError()

    ###
    ### DELETE handlers (examples)
    ### (we use the predefined methods in davcmd instead of doing
    ### a rm directly
    ###

    def delone(self,uri):
        raise NotImplementedError()

    def deltree(self,uri):
        raise NotImplementedError()

    ###
    ### MOVE handlers (examples)
    ###

    def moveone(self,src,dst,overwrite):
        raise NotImplementedError()

    def movetree(self,src,dst,overwrite):
        raise NotImplementedError()

    ###
    ### COPY handlers
    ###

    def copyone(self,src,dst,overwrite):
        raise NotImplementedError()

    def copytree(self,src,dst,overwrite):
        raise NotImplementedError()
    
    def copy(self,src,dst):
        raise NotImplementedError()
    
    def copycol(self, src, dst):
        raise NotImplementedError()
    
    def exists(self,uri):
        raise NotImplementedError()

    def is_collection(self,uri):
       raise NotImplementedError()
