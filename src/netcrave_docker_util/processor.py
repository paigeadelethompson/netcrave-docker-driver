# IAmPaigeAT (paige@paige.bio) 2023

import time
import zmq
import os 
from chacha20poly1305 import ChaCha20Poly1305
import json

class processor():
    def __init__(self, callback = lambda message: True, listen_addr = os.environ.get("PROCESSOR_LISTEN_ADDR")):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._socket.bind(listen_addr)
        self._callback = callback
        self._cip = ChaCha20Poly1305(os.environ.get("NETCRAVE_PRESHARED_KEY"))
        
    def serialize_and_encrypt(self, message): 
        return self._cip.encrypt(os.environ.get("NETCRAVE_NONCE"), json.dumps(message))
    
    def deencrypt_and_deserialize(self, message):
        return self._cip.decrypt(os.environ.get("NETCRAVE_NONCE"), json.dumps(message))
    
    def run(self):
        while True:
            data = self._socket.recv()
            message = self.deencrypt_and_deserialize(message)
            self._callback(message)
            time.sleep(1)
        self._socket.close()
