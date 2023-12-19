# IAmPaigeAT (paige@paige.bio) 2023

from flask import Flask, request, Response
from ssl import SSLContext as ssl_context
from netcrave_docker_util.crypt import shared_secret_crypto
import functools

class netcrave_flask(Flask):
    def route(self, rule, **options):
        f = super().route
        @functools.wraps(f)
        def _map(rule, **options):
            return f(rule, **options)
        return _map
    
    def health_check(self):
        return Response(status = 204)
    
    """
    Used by the HTTP server XXX
    """
    def get_ssl_context(self):
        return self._ssl_context
    
    """
    Issue a client certificate using shared secret crypto for exchange, it's meant to work over HTTP, 
    because it assumes the client does not share a CA even though lots has been done to bootstrap 
    that at this point. 
    """
    def request_client_certificate(self):
        if self._issue_client_certificates == False:
            return Response(status = 501)
        else: 
            sc = shared_secret_crypto()
            """
            XXX - Client PUTs request with CSR, encrypted with shared secret, if shared secret fails, retry with a nonce 
            XXX - of +/- 1 minute, if it then succeeds, the clocks are out of sync on the two hosts, send a 400, otherwise
            XXX send a 202 indicating that the certificates will be created; certificatemgr's job will be to store / retrieve
            XXX certificates in CRDB, and to provide a DAVFS target for the DAVFS filesystem which will be mounted to containers
            XXX and VMs, so there really is nothing left to do at that point.
            """
            
            raise NotImplementedError()
        
    def __init__(self, cert_path = None, key_path = None, ca_path = None, issue_client_certificates = False, *args, **kwargs):
        super(netcrave_flask, self).__init__(*args, **kwargs)
        self._issue_client_certificates = issue_client_certificates
        self._ssl_context = ssl_context()
        self._ssl_context.load_verify_locations(ca_path)
        self._ssl_context.load_cert_chain(cert_path, key_path)
        self.route('/.netcrave/generate_204', view_func = self.health_check, methods = ["HEAD"])
        self.route('/.netcrave/request_client_certificate', view_func = self.client_certificate_request, methods = ["POST"])

