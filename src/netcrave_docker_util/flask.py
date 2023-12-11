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
        if request.is_secure:
            return Response(status = 401)
        else:            
            client_req = shared_secret_crypto().decrypt(request.data)
            if client.req.get("csr") != None:
                data = self._ssl_context.generate_client_certificate(client_req.get("csr"))
                encrypted_data = shared_secret_crypto().encrypt(data)
                return Response(status = 200, response = encrypted_data)
            else: 
                return Response(status = 400)
            
    def __init__(self, *args, **kwargs):
        super(netcrave_flask, self).__init__(*args, **kwargs)
        self._ssl_context = ssl_context()
