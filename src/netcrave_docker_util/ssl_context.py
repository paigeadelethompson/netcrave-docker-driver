# IAmPaigeAT (paige@paige.bio) 2023

import OpenSSL
from OpenSSL.SSL import Context, TLS_SERVER_METHOD
from OpenSSL.crypto import PKey, X509, TYPE_RSA
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from ssl import SSLSocket

import datetime
import uuid

class ssl_context(Context):
    def _build_ca(self, hostname = "netcrave.internal"):
        private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 4096,
            backend=default_backend())

        public_key = private_key.public_key()
        
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'netcrave-ca'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-ca'),
        ]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "netcrave-ca"),
        ]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)
        
        builder = builder.add_extension(
            x509.BasicConstraints(ca = True, path_length = None), 
            critical = True)
        
        certificate = builder.sign(
            private_key = private_key, 
            algorithm = hashes.SHA512(),
            backend = default_backend())
        
        return private_key, public_key, certificate
    
    def _generate_private_key_and_certificate(self, ca_private_key, ca_cert, hostname = "*"):
        private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 4096,
            backend = default_backend())

        public_key = private_key.public_key()
        
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-server-certificate')]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "netcrave-ca")]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)
        
        builder = builder.add_extension(
            x509.BasicConstraints(ca = False, path_length = None), 
            critical = True)
        
        certificate = builder.sign(
            private_key = ca_private_key, 
            algorithm = hashes.SHA512(),
            backend = default_backend())
        
        return private_key, public_key, certificate
        
    def generate_client_certificate(self, csr_bytes, client_name):
        (ca_priv_key, _, ca_cert) = this._ca
        
        csr = x509.load_der_x509_csr(csr_bytes)
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave Ephemeral client certificate'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-client-certificate')]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, client_name)]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.issuer_name(ca_cert)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(csr.public_key())
        
        builder = builder.add_extension(
            x509.BasicConstraints(ca = False, path_length = None), 
            critical = True)
        
        certificate = builder.sign(
            private_key = ca_private_key, 
            algorithm = hashes.SHA512(),
            backend = default_backend())
        
        return { 
            "ca_cert": ca_cert.public_bytes(serialization.Encoding.DER), 
            "client_cert": certificate.public_bytes(serialization.Encoding.DER) }
        

    def __init__(self, hostname = "*", ca_cert = None, *args, **kwargs):
        super(ssl_context, self).__init__(method = TLS_SERVER_METHOD, *args, **kwargs)
        
        if ca_cert != None:
            raise NotImplementedError()
        else:
            ca_priv_key, ca_pub_key, ca_cert = self._build_ca()
            
        priv_key, pub_key, cert = self._generate_private_key_and_certificate(ca_priv_key, ca_cert, hostname)

        key = PKey.from_cryptography_key(priv_key)
        self.use_privatekey(key)
        
        _cert = X509.from_cryptography(cert)
        self.use_certificate(_cert)
        
        self.check_privatekey()
        
        #_lib.SSL_CTX_use_certificate(self._context, cert._x509)
        #if not use_result:
        #    self._raise_passphrase_exception()
            
        #use_result = self.use_certificate(cert)
        
        #if not use_result:
        #    _raise_current_error()
        
        self.check_hostname = False
        
        self._ca = (ca_priv_key, ca_pub_key, ca_cert)
        self._server = (priv_key, pub_key, cert)

    def _encode_hostname(self, hostname):
        if hostname is None:
            return None
        elif isinstance(hostname, str):
            return hostname.encode('idna').decode('ascii')
        else:
            return hostname.decode('ascii')

    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None, session=None):
        # SSLSocket class handles server_hostname encoding before it calls
        # ctx._wrap_socket()
        
        self._sock =  self.sslsocket_class._create(
            sock = sock,
            server_side = server_side,
            do_handshake_on_connect = do_handshake_on_connect,
            suppress_ragged_eofs = suppress_ragged_eofs,
            server_hostname = server_hostname,
            context = self,
            session = session)
        return self._sock

    def _wrap_socket(self, *args, **kwargs):
        return self._sock
    
ssl_context.sslsocket_class = SSLSocket
