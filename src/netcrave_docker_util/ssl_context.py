# IAmPaigeAT (paige@paige.bio) 2023

import OpenSSL
from OpenSSL.SSL import Context
from OpenSSL.crypto import PKey, X509, TYPE_RSA
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
import uuid

class ssl_context(Context):
    def _build_ca(self, domain = "netcrave.internal"):
        private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 4096,
            backend=default_backend())

        public_key = private_key.public_key()
        
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave Ephemeral CA'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-ca'),
        ]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
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
    
    def _generate_private_key_and_certificate(self, ca_private_key, ca_cert, domain = "*"):
        private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 4096,
            backend = default_backend())

        public_key = private_key.public_key()
        
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave Ephemeral server certificate'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-server-certificate'),
        ]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.issuer_name(ca_cert)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)
        
        builder = builder.add_extension(
            x509.BasicConstraints(ca = False, path_length = None), 
            critical = True)
        
        certificate = builder.sign(
            private_key = ca_private_key, 
            algorithm = hashes.SHA512(),
            backend = default_backend())
        
    def generate_client_certificate(self, csr_bytes, client_name):
        (ca_priv_key, _, ca_cert) = this._ca
        
        csr = x509.load_der_x509_csr(csr_bytes)
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave Ephemeral client certificate'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'netcrave-client-certificate'),
        ]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, client_name),
        ]))

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
        super(ssl_context, self).__init__(*args, **kwargs)
        
        if ca_cert != None:
            raise NotImplementedError()
        else:
            ca_priv_key, ca_pub_key, ca_cert = self._build_ca()
            priv_key, pub_key, cert = self._generate_private_key_and_certificate(ca_priv_key, hostname)
            
            use_result = _lib.SSL_CTX_use_PrivateKey(self._context, priv_key)
            
            if not use_result:
                self._raise_passphrase_exception()
                
            use_result = _lib.SSL_CTX_use_certificate(self._context, cert)
            
            if not use_result:
                _raise_current_error()
            
            self._ca = (ca_priv_key, ca_pub_key, ca_cert)
            self._server = (priv_key, pub_key, cert)
