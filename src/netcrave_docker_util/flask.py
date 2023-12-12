# IAmPaigeAT (paige@paige.bio) 2023

from flask import Flask, request, Response
#from netcrave_docker_util.ssl_context import ssl_context 
from ssl import SSLContext as ssl_context
from netcrave_docker_util.crypt import shared_secret_crypto

class netcrave_flask(Flask):
    def _health_check(self):
        return Response(status = 204)
    
    def get_ssl_context(self):
        return self._ssl_context
    
    def verify_request(self, request, client_address):
        raise NotImplementedError()
    
    def _create_auth(self, request):
        raise NotImplementedError()
            
    def __init__(self, cert_path, key_path, ca_path, *args, **kwargs):
        super(netcrave_flask, self).__init__(*args, **kwargs)
        self._ssl_context = ssl_context()
        self._ssl_context.load_verify_locations(ca_path)
        self._ssl_context.load_cert_chain(cert_path, key_path)
