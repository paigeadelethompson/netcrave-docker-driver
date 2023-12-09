# IAmPaigeAT (paige@paige.bio) 2023

from chacha20poly1305 import ChaCha20Poly1305
import json, base64
from hashlib import sha512
from time import time

class shared_secret_crypto():
    def nonce(self):
        h = sha512()
        h.update("{}{}".format(int(time() // 30), os.environ.get("PRESHARED_KEY")))
        return h.digest()
    
    def __init__(self):
        self._cip = ChaCha20Poly1305(self.nonce(), os.environ.get("PRESHARED_KEY"))
        
    def encrypt(self, data):
        serialized = json.dumps(data)
        encrypted = self._cip.encrypt(os.environ.get(, serialized)
        serialized_encrypted = base64.encode(encrypted, 'ascii')
        return serialized_encrypted
    
    def decrypt(self, data):
        deserialized = base64.decodebytes(data)
        decrypted = self._cip.decrypt(os.environ.get(self.nonce(), deserialized)
        decrypted_deserialized = json.loads(decrypted)
        return decrypted_deserialized
        
