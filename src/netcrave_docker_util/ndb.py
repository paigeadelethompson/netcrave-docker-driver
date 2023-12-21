# IAmPaigeAT (paige@paige.bio) 2023

import asyncio
import os
import logging
from pyroute2 import NDB
from singleton_decorator import singleton
from contextlib import asynccontextmanager

@singleton
class network_database(): 
    def __init__(self, *args, **kwargs):
        self._log = logging.getLogger(__name__)

        self._sem = asyncio.Lock()
        self._ndb = NDB(db_provider='sqlite3',
                        db_spec='/srv/netcrave/_netcrave/NDB/network.sqlite3',
                        rtnl_debug=os.environ.get("DEBUG") and True or False,
                        log="on",
                        auto_netns=True)
        
        self._ndb.sources.add(netns="_netcrave")
        
    async def __aenter__(self, *args, **kwargs):
        await self._sem.acquire()
        return self._ndb
    
    async def __aexit__(self, *args, **kwargs):
        self._sem.release()        
    
    def __del__(self):
        self._ndb.close()
