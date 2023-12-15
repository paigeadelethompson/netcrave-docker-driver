# IAmPaigeAT (paige@paige.bio) 2023

from chacha20poly1305 import ChaCha20Poly1305
import json, base64
from hashlib import sha512
from time import time

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
import uuid

from pathlib import Path

class shared_secret_crypto():
    def nonce(self):
        h = sha512()
        h.update("{}{}".format(int(time() // 30), os.environ.get("PRESHARED_KEY")))
        return h.digest()
    
    def __init__(self):
        self._cip = ChaCha20Poly1305(self.nonce(), os.environ.get("PRESHARED_KEY"))
        
    def encrypt(self, data):
        serialized = json.dumps(data)
        encrypted = self._cip.encrypt(self.nonce(), serialized)
        serialized_encrypted = base64.encode(encrypted, 'ascii')
        return serialized_encrypted
    
    def decrypt(self, data):
        deserialized = base64.decodebytes(data)
        decrypted = self._cip.decrypt(self.nonce(), deserialized)
        decrypted_deserialized = json.loads(decrypted)
        return decrypted_deserialized
        
class ez_rsa():
    def __init__(self):
        pass
    
    def get_netcrave_certificate(self):
        key = serialization.load_pem_private_key(
            open("/etc/netcrave/ssl/_netcrave.key").read(), 
            password=None, 
            backend=default_backend())

        cert = x509.load_pem_x509_certificate(
            open("/etc/netcrave/ssl/_netcrave.pem").read(), 
            default_backend())
        
        return key, cert
    
    def create_netcrave_default_certificate(self):
        if not (Path("/etc/netcrave/ssl/_netcrave.key").exists()
                and not Path("/etc/netcrave/ssl/_netcrave.pem").exists()):
                return self.create_server_certificate(
                    "netcrave.local"
                    "US",
                    "WA",
                    "Seattle",
                    "Netcrave Communications",
                    "/etc/netcrave/ssl/_netcrave.key",
                    "/etc/netcrave/ssl/_netcrave.pem")
        else:
            raise Exception("can't overwrite existing server certificates")
    
    def create_server_certificate(self, domain, country, state, locality, org, key_file_dest, cert_file_dest):
        if Path(key_file_dest).exists() or Path(cert_file_dest).exists():
            raise Exception("key and/or certificate already exist")
        
        root_key = serialization.load_pem_private_key(
            open("/etc/netcrave/ssl/ca.key").read(), 
            password = None, 
            backend = default_backend())

        root_cert = x509.load_pem_x509_certificate(
            open("/etc/netcrave/ssl/ca.pem").read(), 
            default_backend())

        cert_key = rsa.generate_private_key(
            public_exponent = 65537, 
            key_size = 2048, 
            backend = default_backend())
        
        new_subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org)])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(new_subject)
            .issuer_name(root_cert.issuer)
            .public_key(cert_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime(1950, 1, 1))
            .not_valid_after(datetime.datetime.max)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(domain)]),
                critical=False)
            .sign(root_key, hashes.SHA512(), default_backend()))
            
        with open(key_file_dest, "wb") as f:
            f.write(cert_key.private_bytes(
                encoding = serialization.Encoding.PEM,
                format = serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm = serialization.BestAvailableEncryption(b"_netcrave")))

        with open(cert_file_dest, "wb") as f:
            f.write(cert.public_bytes(
                encoding = serialization.Encoding.PEM))
            
        return self
    
    def create_default_ca(self):
        private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 4096,
            backend = default_backend())
        
        public_key = private_key.public_key()
        builder = x509.CertificateBuilder()
        
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave CA'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'_netcrave'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Netcrave internal CA')]))
        
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'netcrave')]))
        
        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)
        
        builder = builder.add_extension(
            x509.BasicConstraints(ca = True, path_length = None), critical = True)
        
        certificate = builder.sign(
            private_key = private_key, algorithm=hashes.SHA512(),
            backend=default_backend())
        
        with open("/etc/netcrave/ssl/ca.key", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm = serialization.BestAvailableEncryption(b"_netcrave")))

        with open("/etc/netcrave/ssl/ca.pem", "wb") as f:
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM))
            
        return self
