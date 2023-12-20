# IAmPaigeAT (paige@paige.bio) 2023

import datetime
import uuid
import logging
import aiofiles
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from singleton_decorator import singleton

@singleton
class ez_rsa():
    async def get_netcrave_certificate(self):
        return await self.load_key_and_certificate("/etc/netcrave/ssl/_netcrave.key",
                                                  "/etc/netcrave/ssl/_netcrave.pem")
    
    async def netcrave_certificate(self):
        if not (Path("/etc/netcrave/ssl/ca.key").exists()
                and not Path("/etc/netcrave/ssl/ca.pem").exists()):
            await self.create_default_ca()
            
        if not (Path("/etc/netcrave/ssl/_netcrave.key").exists()
                and not Path("/etc/netcrave/ssl/_netcrave.pem").exists()):
            return await self.create_server_certificate(
                domain="netcrave.local",
                country="US",
                state="WA",
                locality="Seattle",
                org="Netcrave Communications",
                key_file_dest="/etc/netcrave/ssl/_netcrave.key",
                cert_file_dest="/etc/netcrave/ssl/_netcrave.pem")
        else:
            return self

    async def load_key_and_certificate(self, key_path, cert_path): 
        async with aiofiles.open(key_path, "rb") as key_data:
            root_key = serialization.load_pem_private_key(
                await key_data.read(),
                password=None,
                backend=default_backend())
            async with aiofiles.open(cert_path, "rb") as cert_data:
                root_cert = x509.load_pem_x509_certificate(
                    cert_data.read(),
                    default_backend())
                return root_key, root_cert
            
    async def save_key_and_certificate(self, key_dest, cert_dest, key, cert):
        async with aiofiles.open(key_dest, "wb") as key_file:
            await key_file.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()))
            async with aiofiles.open(cert_dest, "wb") as cert_file:
                await cert_file.write(cert.public_bytes(
                encoding=serialization.Encoding.PEM))

    async def create_server_certificate(self, domain, country, state, locality, org, key_file_dest, cert_file_dest):
        log = logging.getLogger(__name__)
        
        if Path(key_file_dest).exists() or Path(cert_file_dest).exists():
            log.info("netcrave-docker certificate already exists, not creating")
            return self
        
        root_key, root_cert = await self.load_key_and_certificate("/etc/netcrave/ssl/ca.key", 
                                                                  "/etc/netcrave/ssl/ca.pem")
        
        cert_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend())

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

        await self.save_key_and_certificate(key_file_dest, cert_file_dest, cert_key, cert)
        return self

    async def create_default_ca(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend())

        public_key = private_key.public_key()
        builder = x509.CertificateBuilder()

        builder = builder.subject_name(
            x509.Name(
                [x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave CA'),
                 x509.NameAttribute(
                     NameOID.ORGANIZATION_NAME, u'_netcrave'),
                 x509.NameAttribute(
                     NameOID.ORGANIZATIONAL_UNIT_NAME,
                    u'Netcrave internal CA')]))

        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'netcrave')]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)

        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True)

        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA512(),
            backend=default_backend())

        await self.save_key_and_certificate("/etc/netcrave/ssl/ca.key", 
                                            "/etc/netcrave/ssl/ca.pem", 
                                            private_key,
                                            certificate)
        return self
