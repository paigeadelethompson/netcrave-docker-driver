# IAmPaigeAT (paige@paige.bio) 2023

from chacha20poly1305 import ChaCha20Poly1305
import json
import base64
from hashlib import sha512
from time import time


class shared_secret_crypto():
    async def nonce(self):
        h = sha512()
        h.update(int(time() // 30))
        return h.digest()

    async def __init__(self):
         if os.environ.get("PRESHARED_KEY") == None:
            raise Exception("missing pre-shared key")
        self._cip = ChaCha20Poly1305(self.nonce(), os.environ.get("PRESHARED_KEY"))
        
    async def encrypt(self, data):
        serialized = json.dumps(data)
        encrypted = self._cip.encrypt(self.nonce(), serialized)
        serialized_encrypted = base64.encode(encrypted, 'ascii')
        return serialized_encrypted
    
    async def decrypt(self, data):
        deserialized = base64.decodebytes(data)
        decrypted = self._cip.decrypt(self.nonce(), deserialized)
        decrypted_deserialized = json.loads(decrypted)
        return decrypted_deserialized
        
